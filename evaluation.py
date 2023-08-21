import json
from statistics import mean
from pathlib import Path
from pprint import pprint
import numpy
import SimpleITK as sitk
import numpy as np
import scipy
 
INPUT_DIRECTORY="/input"  
OUTPUT_DIRECTORY="/output" 

"""
The evaluation code used for the SPPIN2023 leaderboard. The evaluation metrics are based on https://github.com/hjkuijf/ADAMchallenge/blob/master/evaluation_segmentation.py""
"""

def get_hausdorff(gt, seg):
    #Compute the Hausdorff distance.
    
    result_statistics = sitk.StatisticsImageFilter()
    result_statistics.Execute(seg)
    if result_statistics.GetSum() == 0:
        hd = np.nan
        return hd
        # Edge detection is done by ORIGINAL - ERODED, keeping the outer boundaries of lesions. Erosion is performed in 3D
    e_test_image = sitk.BinaryErode(gt, (1, 1, 1))
    e_result_image = sitk.BinaryErode(seg, (1, 1, 1))

    h_test_image = sitk.Subtract(gt, e_test_image)
    h_result_image = sitk.Subtract(seg, e_result_image)

    h_test_indices = np.flip(np.argwhere(sitk.GetArrayFromImage(h_test_image))).tolist()
    h_result_indices = np.flip(np.argwhere(sitk.GetArrayFromImage(h_result_image))).tolist()

    test_coordinates = [gt.TransformIndexToPhysicalPoint(x) for x in h_test_indices]
    result_coordinates = [gt.TransformIndexToPhysicalPoint(x) for x in h_result_indices]

    def get_distances_from_a_to_b(a, b):
        kd_tree = scipy.spatial.KDTree(a, leafsize=100)
        return kd_tree.query(b, k=1, eps=0, p=2)[0]

    d_test_to_result = get_distances_from_a_to_b(test_coordinates, result_coordinates)
    d_result_to_test = get_distances_from_a_to_b(result_coordinates, test_coordinates)

    hd = max(np.percentile(d_test_to_result, 95), np.percentile(d_result_to_test, 95))
    
    
    return hd

def get_dsc(test_image, result_image):
    """Compute the Dice Similarity Coefficient."""
    
    test_array = sitk.GetArrayFromImage(test_image).flatten()
    result_array = sitk.GetArrayFromImage(result_image).flatten()

    return 1.0 - scipy.spatial.distance.dice(test_array, result_array)
    
    
def get_vs(test_image, result_image):
    """Volumetric Similarity.
    
    VS = 1 -abs(A-B)/(A+B)
    
    A = ground truth
    B = predicted     
    """
    
    test_statistics = sitk.StatisticsImageFilter()
    result_statistics = sitk.StatisticsImageFilter()
    
    test_statistics.Execute(test_image)
    result_statistics.Execute(result_image)
    
    numerator = abs(test_statistics.GetSum() - result_statistics.GetSum())
    denominator = test_statistics.GetSum() + result_statistics.GetSum()
    
    if denominator > 0:
        vs = 1 - float(numerator) / denominator
    else:
        vs = np.nan
            
    return vs

def main():
    print_inputs()

    metrics = {"case": {}}
    predictions = read_predictions()

    for job in predictions:
        # Iterate over each algoritm job. The jobs are not in order.

        t1 = get_image_name(values=job["inputs"], slug="pediatric-abdominal-mri-t1")
        t2 = get_image_name(values=job["inputs"], slug="pediatric-abdominal-mri-t2")
        b0 = get_image_name(values=job["inputs"], slug="pediatric-abdominal-mri-dwi-b0")
        b100 = get_image_name(values=job["inputs"], slug="pediatric-abdominal-mri-dwi-b100")

        # Parse one of the filenames to get the batch ID, you could cross-check with the others
        batch_id = "_".join(t1.split("_")[ii].split(".")[0] for ii in [1, 4])
        pprint(f"Processing batch {batch_id}")

        pprint((t1, t2, b0, b100, ))

        # Get location of the inference of the users and load the generated predictions
        segmentation_location = get_file_location(job_pk=job["pk"], values=job["outputs"], slug="mri-segmentation-of-pediatric-neuroblastoma")
        pprint((segmentation_location,))

        segmentation = load_image(location=segmentation_location)
        pprint(segmentation)

        # Read the ground truth, which is present in the container
        ground_truth = load_image(location=f"ground-truth/{batch_id}") 
        pprint(ground_truth)

        # Compare the ground truth with the predictions and calculate the scores
        metrics["case"][batch_id] = {"Dice": get_dsc(ground_truth,segmentation),
                                     "Hausdorff": get_hausdorff(ground_truth, segmentation),
                                     "Volumetric_similarity": get_vs(ground_truth,segmentation)}
    
        
        print("")

    # Now generate an overall score
    metrics["aggregates"] = {"Dice": { 
                             "mean":numpy.nanmedian([batch["Dice"] for batch in metrics["case"].values()]),
                             'std':  numpy.nanstd([batch["Dice"] for batch in metrics["case"].values()])
                             },
        
                             "Hausdorff": {
                                 "mean": numpy.nanmedian([batch["Hausdorff"] for batch in metrics["case"].values()]),
                                  "std": numpy.nanstd([batch["Hausdorff"] for batch in metrics["case"].values()])
                                  },
                             
                             "Volumetric_similarity": {
                                "mean":numpy.nanmedian([batch["Volumetric_similarity"] for batch in metrics["case"].values()]),
                                 "std": numpy.std([batch["Volumetric_similarity"] for batch in metrics["case"].values()])
                                 }
                             }
    pprint(metrics)

    write_metrics(metrics=metrics)

    return 0

def print_inputs():
    # Just for convenience, in the logs you can then see what files you have to work with
    input_files = [str(x) for x in Path(INPUT_DIRECTORY).rglob("*.mha") if x.is_file()]

    print("Input Files:")
    pprint(input_files)
    print("")

def read_predictions():
    # The predictions file tells us the location of the users predictions
    with open(f"{INPUT_DIRECTORY}/predictions.json") as f:
        return json.loads(f.read())
    
def get_image_name(*, values, slug):
    # This tells us the user-provided name of the input or output image
    for value in values:
        if value["interface"]["slug"] == slug:
            return value["image"]["name"]
    
    raise RuntimeError(f"Image with interface {slug} not found!")

def get_interface_relative_path(*, values, slug):
    # Gets the location of the interface relative to the input or output
    for value in values:
        if value["interface"]["slug"] == slug:
            return value["interface"]["relative_path"]
    
    raise RuntimeError(f"Value with interface {slug} not found!")

def get_file_location(*, job_pk, values, slug):
    # Where a job's output file will be located in the evaluation container
    relative_path = get_interface_relative_path(values=values, slug=slug)
    return f"{INPUT_DIRECTORY}/{job_pk}/output/{relative_path}"

def load_json_file(*, location):
    # Reads a json file
    with open(location) as f:
        return json.loads(f.read())
    
def load_image(*, location):
    mha_files = {f for f in Path(location).glob("*.mha") if f.is_file()}

    if len(mha_files) == 1:
        mha_file = mha_files.pop()
        return sitk.ReadImage(mha_file) 
    elif len(mha_files) > 1:
        raise RuntimeError(
            f"More than one mha file was found in {location!r}"
        )
    else:
        raise NotImplementedError

def write_metrics(*, metrics):
    # Write a json document that is used for ranking results on the leaderboard
    with open("/output/metrics.json", "w") as f:
        f.write(json.dumps(metrics))

if __name__ == "__main__":
    raise SystemExit(main())
