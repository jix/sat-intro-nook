import pandas as pd
import svgwrite

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str)
    parser.add_argument('output', type=str)
    parser.add_argument('--scale-x', type=float, default=5)
    parser.add_argument('--scale-y', type=float, default=5)

    args = parser.parse_args()

    items = pd.read_csv(args.input, index_col='item_id')

    days = int(items['end'].max() + 1)
    positions = int((items['position'] + items['width']).max())

    height = (days + 1) * args.scale_y
    width = (positions + 1) * args.scale_x

    drawing = svgwrite.Drawing(args.output, (width, height))
    drawing.add(drawing.rect((0, 0), (width, height), fill='black'))

    grid = drawing.g(
        stroke='#111',
        stroke_width=0.5,
    )
    drawing.add(grid)

    for i in range(1, positions):
        y_start = args.scale_y * 0.5
        y_end = height - args.scale_y * 0.5
        x = args.scale_x * (i + 0.5)
        grid.add(drawing.line((x, y_start), (x, y_end)))

    for i in range(1, days):
        x_start = args.scale_x * 0.5
        x_end = width - args.scale_x * 0.5
        y = args.scale_y * (i + 0.5)
        grid.add(drawing.line((x_start, y), (x_end, y)))

    item_boxes = drawing.g(
        stroke_width=0.5,
    )
    drawing.add(item_boxes)

    colors = [
        '#1f78b4',
        '#33a02c',
        '#e31a1c',
        '#aaaaaa',
        '#a6cee3',
        '#b2df8a',
        '#fb9a99',
    ]

    for item_id, item in items.iterrows():
        x = args.scale_x * (item.position + 0.5 + 0.1)
        y = args.scale_y * (item.begin + 0.5 + 0.1)
        box_width = args.scale_x * (item.width - 0.2)
        box_height = args.scale_y * (item.end - item.begin + 1 - 0.2)
        item_boxes.add(drawing.rect(
            (x, y), (box_width, box_height), fill=colors[item.type]))

    drawing.save()
