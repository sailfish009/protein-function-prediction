import sys
import os
sys.setrecursionlimit(10000)
# enable if you want to profile the forward pass
# os.environ["CUDA_LAUNCH_BLOCKING"] = "1"

from protfun.models import train_enz_from_grids
from protfun.config import get_config

if __name__ == "__main__":
    config_filepath = os.path.join(os.path.dirname(__file__), 'experiments', 'example_gconfig.yaml')
    config = get_config(config_filepath)
    train_enz_from_grids(config, model_name="my_example_model")
