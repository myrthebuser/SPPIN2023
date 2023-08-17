#Docker Submission

We ask participants for our challenge to prepare as a docker submission. This docker can be submitted to Grand Challenge for automatic evaluation.

#Preparing the code
The Python script process.py will handle in- and output of your docker. The specific segmentation method can be changed in the predict function. Please note that the images need to match the size of the T1 image, even though all four images are imported. Also note that the resulting output segmentation needs to be binary.

#Package your algorithm
After you prepared your code you can build the container by using the bash command ./build.sh . 
Next, you can test your container locally by changing the in- and output directory and running the command ./test.sh . Please make sure that you build the docker container first. 
After testing you can build the docker container by running ./export.sh.

For more information please go to https://comic.github.io/evalutils/usage.html .

#Submit your algoritm.
You can submit your algorithm on the SPPIN website. If you followed the steps under 'Package your algorithm' you will get a .tar.gz file. This file can be uploaded to the Grand Challenge platform. Make sure that you submit to the correct phase (either the preliminary test phase or the final test phase). More information can be found on https://grand-challenge.org/documentation/making-a-challenge-submission/ . 
