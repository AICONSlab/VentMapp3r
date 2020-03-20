# Local Install

## Python
For the main required Python packages (numpy, scipy, etc.) we recommend using
[Anaconda for Python 3.6](https://www.continuum.io/downloads)

## Installing package and dependencies for VentMapp3r locally

1. Clone repository

        git clone https://github.com/mgoubran/VentMapp3r.git VentMapp3r

        (or install zip file and uncompress)

        cd VentMapp3r

    If you want to create a virtual environment where VentMapp3r can be run,

        conda create -n ventmapper python=3.6 anaconda
        source activate ventmapper
    
    To end the session,
    
        source deactivate
    
    To remove the environment
    
        conda env remove --name ventmapper

2. Install dependencies
    
        pip install git+https://www.github.com/keras-team/keras-contrib.git
    
    If the computer you are using has a GPU:
        
        pip install -e .[ventmapper_gpu]

    If not:
    
        pip install -e .[ventmapper]

3. Test the installation by running

        ventmapper --help
        
   To confirm that the command line function works, and
   
        ventmapper
        
   To launch the interactive GUI.

## Download deep models

Download the models from [this link](https://drive.google.com/drive/folders/11ZiMEHEwNAbl0KfWJ0CS32rPiMUB34rO?usp=sharing) and place them in the "models" directory

## For tab completion
    pip3 install argcomplete
    activate-global-python-argcomplete

## Updating VentMapp3r
To update VentMapp3r, navigate to the directory where VentMapp3r was cloned and run

    git pull
    pip install -e .[{option}] -process-dependency-links
    
where "option" is dependent on whether or not you have a GPU (see package installation steps above)
