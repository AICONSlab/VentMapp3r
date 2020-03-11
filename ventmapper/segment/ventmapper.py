#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# coding: utf-8

import argcomplete
import argparse
import glob
import nibabel as nib
import numpy as np
import os
import sys
from datetime import datetime
from nilearn.image import reorder_img, resample_img, resample_to_img, math_img, smooth_img, \
    largest_connected_component_img
from nipype.interfaces.c3 import C3d
from pathlib import Path
from scipy import ndimage
import functools
from termcolor import colored
import subprocess


from ventmapper.deep.predict import run_test_case
from ventmapper.qc import seg_qc
from ventmapper.utils import endstatement

os.environ['TF_CPP_MIN_LOG_LEVEL'] = "3"


def parsefn():
    parser = argparse.ArgumentParser(usage='%(prog)s -s [ subj ] \n\n'
                                           "Segment ventricles using a trained CNN")

    optional = parser.add_argument_group('optional arguments')

    optional.add_argument('-s', '--subj', type=str, metavar='', help="input subject")
    optional.add_argument('-fl', '--flair', type=str, metavar='dir', help="input Flair")
    optional.add_argument('-t1', '--t1w', type=str, metavar='', help="input T1-weighted")
    optional.add_argument('-t2', '--t2w', type=str, metavar='', help="input T2-weighted")
    optional.add_argument('-m', '--mask', type=str, metavar='', help="brain mask")
    optional.add_argument('-o', '--out', type=str, metavar='', help="output prediction")
    optional.add_argument('-f', '--force', help="overwrite existing segmentation", action='store_true')
    optional.add_argument('-ss', '--session', type=str, metavar='', help="input session for longitudinal studies")

    # optional.add_argument("-h", "--help", action="help", help="Show this help message and exit")

    return parser


def parse_inputs(parser, args):
    if isinstance(args, list):
        args = parser.parse_args(args)
    argcomplete.autocomplete(parser)

    # check if subj or t1w are given
    if (args.subj is None) and (args.t1w is None):
        sys.exit('subj (-s) or t1w (-t1) must be given')

    # get subject dir if cross-sectional or longitudinal
    if args.subj:
        if args.session:
            subj_dir = os.path.abspath(glob.glob(os.path.join(args.subj, '*%s' % args.session))[0])
        else:
            subj_dir = os.path.abspath(args.subj)
    else:
        subj_dir = os.path.abspath(os.path.dirname(args.t1w))

    subj = os.path.basename(subj_dir)
    print('\n input subject:', subj)

    t1 = args.t1w if args.t1w is not None else '%s/%s_T1_nu.nii.gz' % (subj_dir, subj)
    assert os.path.exists(t1), "%s does not exist ... please check path and rerun script" % t1

    if args.subj is not None:
        fl = '%s/%s_T1acq_nu_FL.nii.gz' % (subj_dir, subj)
        t2 = '%s/%s_T1acq_nu_T2.nii.gz' % (subj_dir, subj)
    else:
        fl = args.flair
        t2 = args.t2w

    mask = args.mask if args.mask is not None else '%s/%s_T1acq_nu_HfB_pred.nii.gz' % (subj_dir, subj)
    assert os.path.exists(mask), "%s does not exist ... please check path and rerun script" % mask

    out = args.out if args.out is not None else None

    force = True if args.force else False

    # return subj_dir, subj, t1, fl, mask, out, force
    return subj_dir, subj, t1, fl, t2, mask, out, force

def orient_img(in_img_file, orient_tag, out_img_file):
    c3 = C3d()
    c3.inputs.in_file = in_img_file
    c3.inputs.args = "-orient %s" % orient_tag
    c3.inputs.out_file = out_img_file
    c3.run()

def check_orient(in_img_file, r_orient, l_orient, out_img_file):
    """
    Check image orientation and re-orient if not in standard orientation (RPI or LPI)
    :param in_img_file: input_image
    :param r_orient: right ras orientation
    :param l_orient: left las orientation
    :param out_img_file: output oriented image
    """
    res = subprocess.run('c3d %s -info' % in_img_file, shell=True, stdout=subprocess.PIPE)
    out = res.stdout.decode('utf-8')
    ort_str = out.find('orient =') + 9
    img_ort = out[ort_str:ort_str + 3]

    cp_orient = False
    if (img_ort != r_orient) and (img_ort != l_orient):
        print("\n Warning: input image is not in RPI or LPI orientation.. "
              "\n re-orienting image to standard orientation based on orient tags (please make sure they are correct)")

        if img_ort == 'Obl':
            img_ort = out[-5:-2]
            orient_tag = 'RPI' if 'R' in img_ort else 'LPI'
        else:
            orient_tag = 'RPI' if 'R' in img_ort else 'LPI'
        print(orient_tag)
        orient_img(in_img_file, orient_tag, out_img_file)
        cp_orient = True
    return cp_orient


def resample(image, new_shape, interpolation="linear"):
    print("\n resampling ...")
    input_shape = np.asarray(image.shape, dtype=image.get_data_dtype())
    ras_image = reorder_img(image, resample=interpolation)
    output_shape = np.asarray(new_shape)
    new_spacing = input_shape / output_shape
    new_affine = np.copy(ras_image.affine)
    new_affine[:3, :3] = ras_image.affine[:3, :3] * np.diag(new_spacing)

    return resample_img(ras_image, target_affine=new_affine, target_shape=output_shape, interpolation=interpolation)

def image_mask(img, mask, img_masked):
    print("\n skull stripping ...")
    c3 = C3d()
    c3.inputs.in_file = img
    c3.inputs.args = "%s -multiply" % mask
    c3.inputs.out_file = img_masked
    c3.run()

def image_standardize(img, mask, img_std):
    print("\n standardization ...")
    c3 = C3d()
    c3.inputs.in_file = img
    c3.inputs.args = "%s -nlw 25x25x25 %s -times -replace nan 0" % (mask, mask)
    c3.inputs.out_file = img_std
    c3.run()

def trim(img, out, voxels=1):
    print("\n cropping ...")
    c3 = C3d()
    c3.inputs.in_file = img
    c3.inputs.args = "-trim %svox" % voxels
    c3.inputs.out_file = out
    c3.run()

def trim_like(img, ref, out, interp = 0):
    print("\n cropping ...")
    c3 = C3d()
    c3.inputs.in_file = ref
    c3.inputs.args = "-int %s %s -reslice-identity" % (interp, img)
    c3.inputs.out_file = out
    c3.run()

def copy_orient(in_img_file, ref_img_file, out_img_file):
    print("\n copy orientation ...")
    c3 = C3d()
    c3.inputs.in_file = ref_img_file
    c3.inputs.args = "%s -copy-transform -type uchar" % in_img_file
    c3.inputs.out_file = out_img_file
    c3.run()

def main(args):
    parser = parsefn()
    subj_dir, subj, t1, fl, t2, mask, out, force = parse_inputs(parser, args)
    cp_orient = False

    if out is None:
        prediction = '%s/%s_T1acq_nu_ventricles_pred.nii.gz' % (subj_dir, subj)
        prediction_std_orient = '%s/%s_T1acq_nu_ventricles_pred_std_orient.nii.gz' % (subj_dir, subj)
    else:
        prediction = out
        prediction_std_orient = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(out).split('.')[0])

    if os.path.exists(prediction) and force is False:
        print("\n %s already exists" % prediction)
    else:
        start_time = datetime.now()

        file_path = os.path.realpath(__file__)
        hyper_dir = Path(file_path).parents[2]

        # if fl is None or t2 is None:
        if fl is None and t2 is None:
            test_seqs = [t1]
            training_mods = ["t1"]
            model_name = 'vent_t1only'
            print("\n found only t1-w, using the %s model" % model_name)
        elif t2 is None and fl:
            test_seqs = [t1, fl]
            training_mods = ["t1", "flair"]
            model_name = 'vent_t1fl'
            print("\n found the t1-w and FLAIR, using the t1-flair model")
        else:
            test_seqs = [t1, fl, t2]
            training_mods = ["t1", "flair", "t2"]
            model_name = 'vent_multi'
            print("\n found all 3 sequences, using the model with all 3 sequences")

        model_json = '%s/models/%s_model.json' % (hyper_dir, model_name)
        model_weights = '%s/models/%s_model_weights.h5' % (hyper_dir, model_name)

        assert os.path.exists(model_json), "%s does not exist ... please download and rerun script" % model_json
        assert os.path.exists(model_weights), \
            "%s model does not exist ... please download and rerun script" % model_weights

        # pred preprocess dir
        print(colored("\n pre-processing ...", 'green'))
        pred_dir = '%s/pred_process' % os.path.abspath(subj_dir)
        if not os.path.exists(pred_dir):
            os.mkdir(pred_dir)

        # standardize intensity and mask data
        c3 = C3d()

        pred_shape = [128, 128, 128]
        # std orientations
        r_orient = 'RPI'
        l_orient = 'LPI'

        # check orientation t1 and mask
        t1_ort = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(t1).split('.')[0])
        cp_orient = check_orient(t1, r_orient, l_orient, t1_ort)
        mask_ort = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(mask).split('.')[0])
        cp_orient_m = check_orient(mask, r_orient, l_orient, mask_ort)
        in_mask = mask_ort if os.path.exists(mask_ort) else mask

        # loading t1
        in_t1 = t1_ort if os.path.exists(t1_ort) else t1
        t1_img = nib.load(in_t1)

        test_data = np.zeros((1, len(training_mods), pred_shape[0], pred_shape[1], pred_shape[2]), dtype=t1_img.get_data_dtype())

        for s, seq in enumerate(test_seqs):
            print(colored("\n pre-processing %s" % os.path.basename(seq).split('.')[0], 'green'))

            seq_ort = "%s/%s_std_orient.nii.gz" % (subj_dir, os.path.basename(seq).split('.')[0])
            if training_mods[s] != 't1':
                # check orientation
                cp_orient_seq = check_orient(seq, r_orient, l_orient, seq_ort)
            in_seq = seq_ort if os.path.exists(seq_ort) else seq

            # masked
            seq_masked = "%s/%s_masked.nii.gz" % (pred_dir, os.path.basename(seq).split('.')[0])
            image_mask(in_seq, in_mask, seq_masked)

            # standardized
            seq_std = "%s/%s_masked_standardized.nii.gz" % (pred_dir, os.path.basename(seq).split('.')[0])
            image_standardize(seq_masked, in_mask, seq_std)

            # cropping
            if training_mods[s] == 't1':
                seq_crop = '%s/%s_masked_standardized_cropped.nii.gz' % (pred_dir, os.path.basename(seq).split('.')[0])
                trim(seq_std, seq_crop, voxels=1)
            else:
                seq_crop = '%s/%s_masked_standardized_cropped.nii.gz' % (pred_dir, os.path.basename(seq).split('.')[0])
                ref_file = '%s/%s_masked_standardized_cropped.nii.gz' % (pred_dir, os.path.basename(t1).split('.')[0])
                trim_like(seq_std, ref_file, seq_crop, interp=1)

            # resampling
            img = nib.load(seq_crop)
            res = resample(img, [pred_shape[0], pred_shape[1], pred_shape[2]])
            seq_res = '%s/%s_resampled.nii.gz' % (pred_dir, os.path.basename(seq).split('.')[0])
            nib.save(res, seq_res)

            if not os.path.exists(seq_res):
                print("\n pre-processing %s" % training_mods[s])
                c3.run()
            res_data = nib.load(seq_res)
            test_data[0, s, :, :, :] = res_data.get_data()

        print(colored("\n generating ventricle segmentation", 'green'))

        res_t1_file = '%s/%s_resampled.nii.gz' % (pred_dir, os.path.basename(t1).split('.')[0])
        res = nib.load(res_t1_file)

        pred = run_test_case(test_data=test_data, model_json=model_json, model_weights=model_weights,
                             affine=res.affine, output_label_map=True, labels=1)

        # resample back
        pred_res = resample_to_img(pred, t1_img, interpolation="linear")
        pred_prob_name = os.path.join(pred_dir, "%s_%s_pred_prob.nii.gz" % (subj, model_name))
        nib.save(pred_res, pred_prob_name)

        pred_res_th = math_img('img > 0.5', img=pred_res)
        pred_name = os.path.join(pred_dir, "%s_%s_pred.nii.gz" % (subj, model_name))
        nib.save(pred_res_th, pred_name)

        # copy original orientation to final prediction
        if cp_orient:
            nib.save(pred_res_th, prediction_std_orient)
            copy_orient(pred_name, t1, prediction)
        else:
            nib.save(pred_res_th, prediction)

        print("\n generating mosaic image for qc")

        seg_qc.main(['-i', '%s' % t1, '-s', '%s' % prediction, '-g', '2', '-m', '40'])

        endstatement.main('Ventricles prediction and mosaic generation', '%s' % (datetime.now() - start_time))


if __name__ == "__main__":
    main(sys.argv[1:])
