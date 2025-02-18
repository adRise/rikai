#  Copyright 2021 Rikai Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from torchvision import transforms as T

from rikai.contrib.torch.transforms.utils import uri_to_pil

__all__ = ["pre_processing", "post_processing"]

pre_processing = T.Compose(
    [
        uri_to_pil,
        T.Resize(256),
        T.CenterCrop(224),
        T.ToTensor(),
    ]
)


def post_processing(batch):
    results = []
    for predicts in batch:
        predict_result = {
            "boxes": [],
            "labels": [],
            "scores": [],
        }
        for box, label, score in zip(
            predicts["boxes"].tolist(),
            predicts["labels"].tolist(),
            predicts["scores"].tolist(),
        ):
            predict_result["boxes"].append(box)
            predict_result["labels"].append(label)
            predict_result["scores"].append(score)

        results.append(predict_result)
    return results
