#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 11 09:28:09 2023

@author: myrthebuser
SPPIN Example Submission

Please only change things on the places were it is indicated.
"""

# Copyright 2023 Radboud University Medical Center
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from dataclasses import dataclass, make_dataclass
from enum import Enum
from typing import Any, Dict
from pathlib import Path

import SimpleITK

INPUT_PREFIX = Path('/input')
OUTPUT_PREFIX = Path('/output')

class IOKind(str, Enum):
    JSON = "JSON"
    IMAGE = "Image"
    FILE = "File"

class InterfaceKind(str, Enum):
    def __new__(cls, value, annotation, io_kind):
        member = str.__new__(cls, value)
        member._value_ = value
        member.annotation = annotation
        member.io_kind = io_kind
        return member

    STRING = "String", str, IOKind.JSON
    INTEGER = "Integer", int, IOKind.JSON
    FLOAT = "Float", float, IOKind.JSON
    BOOL = "Bool", bool, IOKind.JSON
    ANY = "Anything", Any, IOKind.JSON
    CHART = "Chart", Dict[str, Any], IOKind.JSON

    # Annotation Types
    TWO_D_BOUNDING_BOX = "2D bounding box", Dict[str, Any], IOKind.JSON
    MULTIPLE_TWO_D_BOUNDING_BOXES = "Multiple 2D bounding boxes", Dict[str, Any], IOKind.JSON
    DISTANCE_MEASUREMENT = "Distance measurement", Dict[str, Any], IOKind.JSON
    MULTIPLE_DISTANCE_MEASUREMENTS = "Multiple distance measurements", Dict[str, Any], IOKind.JSON
    POINT = "Point", Dict[str, Any], IOKind.JSON
    MULTIPLE_POINTS = "Multiple points", Dict[str, Any], IOKind.JSON
    POLYGON = "Polygon", Dict[str, Any], IOKind.JSON
    MULTIPLE_POLYGONS = "Multiple polygons", Dict[str, Any], IOKind.JSON
    LINE = "Line", Dict[str, Any], IOKind.JSON
    MULTIPLE_LINES = "Multiple lines", Dict[str, Any], IOKind.JSON
    ANGLE = "Angle", Dict[str, Any], IOKind.JSON
    MULTIPLE_ANGLES = "Multiple angles", Dict[str, Any], IOKind.JSON
    ELLIPSE = "Ellipse", Dict[str, Any], IOKind.JSON
    MULTIPLE_ELLIPSES = "Multiple ellipses", Dict[str, Any], IOKind.JSON

    # Choice Types
    CHOICE = "Choice", int, IOKind.JSON
    MULTIPLE_CHOICE = "Multiple choice", int, IOKind.JSON

    # Image types
    IMAGE = "Image", bytes, IOKind.IMAGE
    SEGMENTATION = "Segmentation", bytes, IOKind.IMAGE
    HEAT_MAP = "Heat Map", bytes, IOKind.IMAGE

    # File types
    PDF = "PDF file", bytes, IOKind.FILE
    SQREG = "SQREG file", bytes, IOKind.FILE
    THUMBNAIL_JPG = "Thumbnail jpg", bytes, IOKind.FILE
    THUMBNAIL_PNG = "Thumbnail png", bytes, IOKind.FILE
    OBJ = "OBJ file", bytes, IOKind.FILE
    MP4 = "MP4 file", bytes, IOKind.FILE

    # Legacy support
    CSV = "CSV file", str, IOKind.FILE
    ZIP = "ZIP file", bytes, IOKind.FILE

@dataclass
class Interface:
    slug: str
    relative_path: str
    kind: InterfaceKind

    @property
    def kwarg(self):
        return self.slug.replace("-", "_").lower()

    def load(self):
        if self.kind.io_kind == IOKind.JSON:
            return self._load_json()
        elif self.kind.io_kind == IOKind.IMAGE:
            return self._load_image()
        elif self.kind.io_kind == IOKind.FILE:
            return self._load_file()
        else:
            raise AttributeError(f"Unknown io kind {self.kind.io_kind!r} for {self.kind!r}")

    def save(self, *, data):
        if self.kind.io_kind == IOKind.JSON:
            return self._save_json(data=data)
        elif self.kind.io_kind == IOKind.IMAGE:
            return self._save_image(data=data)
        elif self.kind.io_kind == IOKind.FILE:
            return self._save_file(data=data)
        else:
            raise AttributeError(f"Unknown io kind {self.kind.io_kind!r} for {self.kind!r}")

    def _load_json(self):
        with open(INPUT_PREFIX / self.relative_path, "r") as f:
            return json.loads(f.read())

    def _save_json(self, *, data):
        with open(OUTPUT_PREFIX / self.relative_path, "w") as f:
            f.write(json.dumps(data))

    def _load_image(self):
        input_directory = INPUT_PREFIX / self.relative_path

        mha_files = {f for f in input_directory.glob("*.mha") if f.is_file()}

        if len(mha_files) == 1:
            mha_file = mha_files.pop()
            return SimpleITK.ReadImage(mha_file)
        elif len(mha_files) > 1:
            raise RuntimeError(
                f"More than one mha file was found in {input_directory!r}"
            )
        else:
            print(input_directory)
            raise NotImplementedError

    def _save_image(self, *, data):
        output_directory = OUTPUT_PREFIX / self.relative_path

        output_directory.mkdir(exist_ok=True, parents=True)

        SimpleITK.WriteImage(data, output_directory / "overlay.mha")

    @property
    def _file_mode_suffix(self):
        if self.kind.annotation == str:
            return ""
        elif self.kind.annotation == bytes:
            return "b"
        else:
            raise AttributeError(f"Unknown annotation {self.kind.annotation!r} for {self.kind!r}")

    def _load_file(self):
        with open(INPUT_PREFIX / self.relative_path, f"r{self._file_mode_suffix}") as f:
            return f.read()

    def _save_file(self, *, data):
        with open(OUTPUT_PREFIX / self.relative_path, f"w{self._file_mode_suffix}") as f:
            f.write(data)

INPUT_INTERFACES = [
    Interface(slug="pediatric-abdominal-mri-t1", relative_path="images/abdominal-mr_t1", kind=InterfaceKind.IMAGE),
    Interface(slug="pediatric-abdominal-mri-t2", relative_path="images/abdominal-mr_t2", kind=InterfaceKind.IMAGE),
    Interface(slug="pediatric-abdominal-mri-dwi-b0", relative_path="images/abdominal-mr_b0", kind=InterfaceKind.IMAGE),
    Interface(slug="pediatric-abdominal-mri-dwi-b100", relative_path="images/abdominal-mr_b100", kind=InterfaceKind.IMAGE),
]

OUTPUT_INTERFACES = [
    Interface(slug="mri-segmentation-of-pediatric-neuroblastoma", relative_path="images/neuroblastoma-segmentation", kind=InterfaceKind.SEGMENTATION),
]

Inputs = make_dataclass(cls_name="Inputs", fields=[(inpt.kwarg, inpt.kind.annotation) for inpt in INPUT_INTERFACES])

Outputs = make_dataclass(cls_name="Outputs", fields=[(output.kwarg, output.kind.annotation) for output in OUTPUT_INTERFACES])

def load() -> Inputs:
    return Inputs(
        **{interface.kwarg: interface.load() for interface in INPUT_INTERFACES}
    )

def predict(*, inputs: Inputs) -> Outputs:
    """ This is the place where you can implement your own algoritme. Please note taht the outputs have to match the size of the T1 images 
    to properly be evaluated. """
    
    # Define the inputs 
    t1 = inputs.pediatric_abdominal_mri_t1
    t2 = inputs.pediatric_abdominal_mri_t2
    dwi_b0 = inputs.pediatric_abdominal_mri_dwi_b0
    dwi_b100 = inputs.pediatric_abdominal_mri_dwi_b100


    # TO DO: Replace the binary threshold with your own segmentation algoritme
    segmentation = SimpleITK.BinaryThreshold(
            image1=t1, lowerThreshold=10, insideValue=0, outsideValue=1
        )

    
    outputs = Outputs(
        mri_segmentation_of_pediatric_neuroblastoma = segmentation
    )

    return outputs

def save(*, outputs: Outputs) -> None:
    for interface in OUTPUT_INTERFACES:
        interface.save(data=getattr(outputs, interface.kwarg))

def main() -> int:
    inputs = load()
    outputs = predict(inputs=inputs)
    save(outputs=outputs)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
