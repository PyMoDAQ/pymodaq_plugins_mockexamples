import argparse
import math

from instrument import Axis, JSONDetector

def int_greater_than_zero(value):
    try:
        value = int(value)
        if value < 1:
            raise argparse.ArgumentTypeError("{} is not 1 or more".format(value))
    except ValueError:
        raise argparse.ArgumentTypeError("{} is not an integer".format(value))
    return value

def get_args() -> dict:
    parser = argparse.ArgumentParser(description="Parse arguments to build a detector and use it with JSON-LECO")

    parser.add_argument(
        "-d", "--dimension",
        type=int,
        choices=[0, 1, 2],
        default=0,
        help="Dimension of the data (0, 1, or 2)"
    )



    parser.add_argument(
        "-x", "--x_axis_len",
        type=int,
        help="Length of x-axis (required if dimension >= 1)"
    )

    parser.add_argument(
        "-y", "--y_axis_len",
        type=int,
        help="Length of y-axis (required if dimension == 2)"
    )

    parser.add_argument(
        "-l", "--labels",
        type=str,
        nargs='+',
        help="Label of each channel of acquired data"
    )

    parser.add_argument(
        "-c", "--channels",
        default=1,
        type=int_greater_than_zero,
        help="Number of signals acquired by the detector (3 channels in 2D = RGB image)"
    )


    parser.add_argument(
        "-n", "--name",
        type=str,
        default="detector",
        help="LECO name for the device")


    args = parser.parse_args()


    if args.dimension >= 1 and args.x_axis_len is None:
        parser.error("x_axis_len is required when dimension is 1 or 2.")
    if args.dimension == 2 and args.y_axis_len is None:
        parser.error("y_axis_len is required when dimension is 2.")

    return vars(args)


def main():
    args  = get_args()
    args['axes'] = []
    if 'y_axis_len' in args and args['y_axis_len']:
        args['axes'].append(Axis.from_size(args['y_axis_len'], label="the y axis", units="pixels"))
    if 'x_axis_len' in args and args['x_axis_len']:
        args['axes'].append(Axis.from_data((lambda l : [((math.exp(i / (l - 1)) - 1) / (math.e - 1)) * l for i in range(l)])(args['x_axis_len']), label="the x axis", units="cm"))
    detector = JSONDetector(**args)
 
    detector.run()


if __name__ == "__main__":
    main()


