import os

from dotenv import load_dotenv


load_dotenv()

inputs = os.getenv('INPUT_PREFIX_FOR_SET_VAL')
prefix_set_val = os.getenv('INPUT_PREFIX_FOR_SET_VAL')
prefix_man_stage = os.getenv('PREFIX_MAN_STAGE_PEEK')
prefix_mpp = os.getenv('PREFIX_MPP')
prefix_mpp_stage = os.getenv('PREFIX_MPP_STAGE')
