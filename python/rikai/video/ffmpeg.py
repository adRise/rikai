#  Copyright 2021 Rikai Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""FFmpeg related types and utils"""

import sys
import numpy as np

try:
    import ffmpeg
except ImportError:
    raise ValueError(
        "Couldn't import ffmpeg. Please make sure to "
        "`pip install ffmpeg-python` explicitly or install "
        "the correct extras like `pip install rikai[all]`"
    )
from rikai.types.vision import Image
from rikai.types.video import VideoSampler


class VideoFrameSampler(VideoSampler):
    """
    An Image sampler returning one from every `sample_rate` video frames.
    """

    def __init__(
        self,
        stream: VideoStream,
        sample_rate: int = 1,
        start_frame: int = 0,
        max_samples: int = -1,
        scale_width: int = -1,
        scale_height: int = -1,
    ):
        """
        Parameters
        ----------
        sample_rate: int
            The sampling rate in number of frames
        start_frame: int
            Start from a specific frame (0-based indexing)
        max_samples: int
            Yield at most this many frames (-1 means no max)
        """
        super().__init__(stream)
        self.sample_rate = sample_rate
        self.start_frame = start_frame
        self.max_samples = max_samples
        self.scale_width = (scale_width,)
        self.scale_height = (scale_height,)
        self.probe = None

    def _probe(self):
        try:
            self.probe = ffmpeg.probe(self.stream.uri)
        except ffmpeg.Error as e:
            print(e.stderr, file=sys.stderr)
            sys.exit(1)
        video_stream = next(
            (
                stream
                for stream in self.probe["streams"]
                if stream["codec_type"] == "video"
            ),
            None,
        )
        if video_stream is None:
            print("No video stream found", file=sys.stderr)
            sys.exit(1)

        self.width = int(video_stream["width"])
        self.height = int(video_stream["height"])
        self.num_frames = int(video_stream["nb_frames"])
        self.duration = int(video_stream["duration"])
        self.frame_rate = np.round(self.duration / self.num_frames).astype(int)

    def load_video(self):
        if not self.probe:
            self._probe()
        video_data, _ = (
            ffmpeg.input(self.stream.uri)
            .filter("scale", self.scale_width, self.scale_height)
            .output(
                "pipe:",
                format="rawvideo",
                pix_fmt="rgb24",
                start_number=self.start_frame,
                vframes=self.start_frame + self.max_samples
                if self.max_samples
                else None,
                r=1 / self.sample_rate,
            )
            .run(capture_stdout=True)
        )
        h = self.height if not self.scale_height else self.scale_height
        w = self.height if not self.scale_width else self.scale_width

        video_array = np.frombuffer(video_data, np.uint8).reshape(
            [-1, h, w, 3]
        )
        return [Image.from_array(arr) for arr in video_array]

    def __iter__(self):
        for frame in iter(self.load_video()):
            yield frame