#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
# coding: utf-8

import argcomplete
import argparse
import glob
import nibabel as nib
import numpy as np
import mahotas as mh
import os
import sys
from datetime import datetime
from nilearn.image import reorder_img, resample_img, resample_to_img, math_img, smooth_img, \
    largest_connected_component_img
from nipype.interfaces.c3 import C3d
from pathlib import Path
from scipy import ndimage
import functools

from hypermatter.deep.predict import run_test_case
from hypermatter.qc import seg_qc
from hypermatter.utils import endstatement

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


def resample(image, new_shape, interpolation="continuous"):
    input_shape = np.asarray(image.shape, dtype=image.get_data_dtype())
    ras_image = reorder_img(image, resample=interpolation)
    output_shape = np.asarray(new_shape)
    new_spacing = input_shape / output_shape
    new_affine = np.copy(ras_image.affine)
    new_affine[:3, :3] = ras_image.affine[:3, :3] * np.diag(new_spacing)

    return resample_img(ras_image, target_affine=new_affine, target_shape=output_shape, interpolation=interpolation)


def extract_from_center(ventricles_img, mask_brain):
    # smoothing
    pred_sm = smooth_img(ventricles_img, fwhm=2)

    # thresold the smoothed mask at 0.45, get the arr for more processing
    pred_th = np.zeros_like(mask_brain.get_data())
    pred_th[pred_sm.get_data() > 0.45] = 1
    pred_th[pred_sm.get_data() <= 0.45] = 0

    # center of mask, dilated
    mask_arr = mask_brain.get_data()
    center_of_mass = ndimage.center_of_mass(mask_arr)
    mask_csf_ball = np.zeros_like(mask_arr)
    mask_csf_ball[int(center_of_mass[0]), int(center_of_mass[1]), int(center_of_mass[2])] = 1
    mask_csf_ball = ndimage.binary_dilation(mask_csf_ball, iterations=10)

    # extract largest object
    label_pred, nr_objects = mh.label(pred_th)
    intersect_labels = np.unique(label_pred[mask_csf_ball])
    pred_component = np.zeros_like(mask_brain)
    pred_component = functools.reduce(np.logical_or, (label_pred == v for v in intersect_labels if v != 0))

    # return result as nifti image
    pred_res = nib.Nifti1Image(pred_component.astype(int), ventricles_img.get_affine(), ventricles_img.header)

    return pred_res

def main(args):
    parser = parsefn()
    subj_dir, subj, t1, fl, t2, mask, out, force = parse_inputs(parser, args)
    # subj_dir, subj, t1, fl, mask, out, force = parse_inputs(parser, args)

    if out is None:
        prediction = '%s/%s_T1acq_nu_ventricles_pred.nii.gz' % (subj_dir, subj)
    else:
        prediction = out

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
            model_name = 'vent_t1'
            print("\n found only t1-w, using the %s model" % model_name)
        elif t2 is None and fl:
            test_seqs = [t1, fl]
            training_mods = ["t1", "flair"]
            model_name = 'vent_t1fl'
            print("\n found the t1-w and FLAIR, using the t1-flair model")
        else:
            test_seqs = [t1, fl, t2]
            training_mods = ["t1", "flair", "t2"]
            model_name = 'vent'
            print("\n found all 3 sequences, using the model with all 3 sequences")

        model_json = '%s/models/%s_model.json' % (hyper_dir, model_name)
        model_weights = '%s/models/%s_model_weights.h5' % (hyper_dir, model_name)

        assert os.path.exists(model_json), "%s does not exist ... please download and rerun script" % model_json
        assert os.path.exists(model_weights), \
            "%s model does not exist ... please download and rerun script" % model_weights

        # pred preprocess dir
        pred_dir = '%s/pred_process' % os.path.abspath(subj_dir)
        if not os.path.exists(pred_dir):
            os.mkdir(pred_dir)

        # standardize intensity and mask data
        c3 = C3d()

        t1_img = nib.load(t1)

        test_data = np.zeros((1, len(training_mods), 128, 128, 128), dtype=t1_img.get_data_dtype())

        # resample t1
        res_t1 = resample(t1_img, [128, 128, 128])
        res_t1_file = '%s/%s_resampled_128iso.nii.gz' % (pred_dir, os.path.basename(t1).split('.')[0])
        res_t1.to_filename(res_t1_file)

        # resample mask
        c3.inputs.in_file = mask
        c3.inputs.args = "-resample 128x128x128mm -interpolation NearestNeighbor -as o %s -push o -copy-transform" % res_t1_file
        res_mask_name = '%s/%s_T1acq_HfB_resampled_128iso.nii.gz' % (pred_dir, subj)
        c3.inputs.out_file = res_mask_name
        c3.run()

        for s, seq in enumerate(test_seqs):
            # resample images
            img = nib.load(seq)
            res = resample(img, [128, 128, 128])
            res_file = '%s/%s_resampled_128iso.nii.gz' % (pred_dir, os.path.basename(seq).split('.')[0])
            if not os.path.exists(res_file):
                res.to_filename(res_file)

            # standardize
            c3.inputs.in_file = res_file
            c3.inputs.args = "%s -nlw 50x50x50 %s -times -replace nan 0" % (res_mask_name, res_mask_name)
            std_file = "%s/%s_masked_resampled_standardized.nii.gz" % (pred_dir, os.path.basename(seq).split('.')[0])
            c3.inputs.out_file = std_file
            # print(c3.cmdline)
            if not os.path.exists(std_file):
                print("\n pre-processing %s" % training_mods[s])
                c3.run()
            std_data = nib.load(std_file)
            test_data[0, s, :, :, :] = std_data.get_data()

        print("\n generating ventricle segmentation")

        pred = run_test_case(test_data=test_data, model_json=model_json, model_weights=model_weights,
                             affine=res.affine, output_label_map=True, labels=1)

        # resample back
        pred_res = resample_to_img(pred, t1_img)
        pred_name = os.path.join(pred_dir, "%s_%s_pred_prob.nii.gz" % (subj, model_name))
        nib.save(pred_res, pred_name)

        mask_img = nib.load(mask)
        pred_comp = extract_from_center(pred_res, mask_img)
        nib.save(pred_comp, prediction)

        print("\n generating mosaic image for qc")

        seg_qc.main(['-i','%s' % t1, '-s', '%s' % prediction, '-g', '2', '-m', '40'])

        endstatement.main('Ventricles prediction and mosaic generation', '%s' % (datetime.now() - start_time))


if __name__ == "__main__":
    main(sys.argv[1:])
