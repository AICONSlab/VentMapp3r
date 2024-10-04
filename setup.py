from setuptools import setup, find_packages
from ventmapper import __version__

setup(
    name='VentMapp3r',
    version=__version__,
    description='A CNN-based segmentation technique using MRI images from BrainLab',
    author=['Maged Goubran', 'Hassan Akhavein', 'Edward Ntiri'],
    author_email='maged.goubran@sri.utoronto.ca',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    license='GNU GENERAL PUBLIC LICENSE v3',
    url='https://github.com/mgoubran/VentMapp3r',  # change later
    download_url='https://github.com/mgoubran/VentMapp3r',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU  General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Unix Shell',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Image Recognition',
    ],
    dependency_links=[
        'git+https://github.com/keras-team/keras-contrib.git'
    ],
    install_requires=[
        'nibabel==3.2.2', 'nipype==1.7.1', 'argparse==1.4.0', 'argcomplete==3.1.2', 'joblib==1.1.1', 'keras==2.2.4', 'nilearn==0.9.2', 'scikit-learn==0.24.2',
        'keras-contrib==2.0.8', 'pandas==1.1.5', 'numpy==1.19.5', 'plotly==5.18.0', 'PyQt5==5.15.6', 'termcolor==1.1.0'
    ],
    extras_require={
        "ventmapper": ["tensorflow==1.4.0"],
        "ventmapper_gpu": ["tensorflow-gpu==1.4.0"],
    },
    entry_points={'console_scripts': ['ventmapper=ventmapper.cli:main']},
    keywords=[
        'neuroscience dementia lesion stroke white-matter-hyperintensity brain-atlas mri neuroimaging',
        'medical-imaging biomedical image-processing image-registration image-segmentation',
    ],
)
