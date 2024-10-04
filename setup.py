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
        'PyQt5==5.15.6', 'PyQt5-Qt5==5.15.15', 'PyQt5-sip==12.9.1', 'argcomplete==3.1.2', 'argparse=1.4.0', 'bleach==1.5.0', 'cached-property==1.5.2', 'certifi==2024.8.30', 'charset-normalizer==2.0.12', 'ci-info==0.2.0', 'click==8.0.4', 'dataclasses==0.8', 'decorator==4.4.2', 'enum34==1.1.10', 'etelemetry==0.2.2', 'filelock==3.4.1', 'h5py==3.1.0', 'html5lib==0.9999999', 'idna==3.10', 'importlib-metadata==4.8.3', 'isodate==0.6.1', 'joblib==1.1.1', 'keras==2.2.4', 'keras-applications==1.0.8', 'keras-contrib==2.0.8', 'keras-preprocessing==1.1.2', 'lxml==5.3.0', 'markdown==3.3.7', 'networkx==2.5.1', 'nibabel==3.2.2', 'nilearn==0.9.2', 'nipype==1.7.1', 'numpy==1.19.5', 'packaging==21.3', 'pandas==1.1.5', 'plotly==5.18.0', 'protobuf==3.19.6', 'prov==2.0.1', 'pydot==1.4.2', 'pyparsing==3.1.4', 'python-dateutil==2.9.0.post0', 'pytz==2024.2', 'pyyaml==6.0.1', 'rdflib==5.0.0', 'requests==2.27.1', 'scikit-learn==0.24.2', 'scipy==1.5.4', 'simplejson==3.19.3', 'six==1.16.0', 'tenacity==8.2.2', 'tensorflow==1.4.0', 'tensorflow-tensorboard==0.4.0', 'termcolor==1.1.0', 'threadpoolctl==3.1.0', 'traits==6.4.1', 'typing-extensions==4.1.1', 'urllib3==1.26.20', 'werkzeug==2.0.3', 'zipp==3.6.0'
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
