# Docker / Singularity

If you intend to use Singularity, scroll down to the Singularity section. Otherwise, the steps to use the image in Docker can be found below.

## Before using Docker image for VentMapp3r

If you want to use Docker to run VentMapp3r, you must first install Docker on your system. While the installation method differs per system, instructions can be found for the following:

- Ubuntu
- Windows 7/8/10 or Windows10Pro
- OS X

Once Docker is installed, open the docker terminal and test it with the command

    docker run hello-world


## Pulling VentMapp3r's Docker immge

While you can download various Docker images, for the sake of this tutorial pull the VentMpp3r image

    docker pull mgoubran/ventmapper:latest

Verify that the image was pulled successfully by checking all images on your system

    docker images


## Running the Docker image

If you have installed Docker for the first time. and have verified that the `hello-world` image was running, then VentMapper can be run on your syste.

The simplest way to run the container is:

    docker run -it mgoubran/ventmapper seg_vent -t1 /VentMapp3r/data/test_case/mprage.nii.gz


## Using VentMapper on Singularity

Docker images can still be used on Singularity. This is especially good if you are processing images using Compute Canada clusters. The following instructions are based on the steps provided on the [Compute Canada wiki](https://docs.computecanada.ca/wiki/Singularity).

Load the specific Singularity module you would like to use.

    module load singularity/3.5

Although VentMapper is stored as a Docker image, it can be built in singularity by calling:

    singularity build ventmapper.sif docker://mgoubran/ventmapper

To ensure that the Docker image has been built in Singularity, run

    singularity exec ventmapper.sif ventmapper --help


