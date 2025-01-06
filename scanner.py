from PIL import Image
import os
import math
from collections import Counter, defaultdict

def color_difference(color1, color2):
    r1, g1, b1, a1 = color1
    r2, g2, b2, a2 = color2
    return math.sqrt((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2 + (2 * (a2 - a1)) ** 2)

def calculate_color_similarities(colors):
    similarities = defaultdict(float)
    for i, color1 in enumerate(colors):
        total_difference = 0
        for j, color2 in enumerate(colors):
            if i != j:
                difference = color_difference(color1, color2)
                total_difference += difference
        similarities[color1] = total_difference / (len(colors) - 1) if len(colors) > 1 else float('inf')
    return similarities

def reduce_colors(colors, percentages, target_count):
    while len(colors) > target_count:
        similarities = calculate_color_similarities(colors)
        most_similar_color = min(similarities.items(), key=lambda x: x[1])[0]
        removed_percentage = percentages[most_similar_color]
        print(f"Removed color RGBA{most_similar_color} ({removed_percentage:.2f}% of non-ignored pixels)")
        colors.remove(most_similar_color)
        del percentages[most_similar_color]
    return colors

def should_ignore_color(color, ignore_list, threshold):
    if not ignore_list:
        return False
    return any(color_difference(color, ignored_color) <= threshold for ignored_color in ignore_list)

def get_color_frequencies(image, ignore_colors, avg_difference_threshold):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    color_count = Counter()
    total_counted_pixels = 0
    for x in range(image.width):
        for y in range(image.height):
            pixel = image.getpixel((x, y))
            if not should_ignore_color(pixel, ignore_colors, avg_difference_threshold):
                color_count[pixel] += 1
                total_counted_pixels += 1
    if total_counted_pixels == 0:
        print("Warning: All pixels matched ignore list!")
        return {}, 0
    color_percentages = {
        color: (count / total_counted_pixels) * 100 
        for color, count in color_count.items()
    }
    return color_percentages, total_counted_pixels

def get_unique_colors(image, avg_difference_threshold, max_colors, min_pixel_percentage, ignore_colors):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    color_percentages, total_counted_pixels = get_color_frequencies(image, ignore_colors, avg_difference_threshold)
    total_pixels = image.width * image.height
    ignored_pixels = total_pixels - total_counted_pixels
    print(f"\nPixel Analysis:")
    print(f"- Total pixels: {total_pixels}")
    print(f"- Ignored pixels: {ignored_pixels} ({(ignored_pixels/total_pixels)*100:.1f}% of image)")
    print(f"- Considered pixels: {total_counted_pixels} ({(total_counted_pixels/total_pixels)*100:.1f}% of image)")
    valid_colors = {
        color: percentage 
        for color, percentage in color_percentages.items() 
        if percentage >= min_pixel_percentage
    }
    colors = list(valid_colors.keys())
    if len(colors) > max_colors:
        print(f"\nReducing from {len(colors)} colors to {max_colors} colors:")
        colors = reduce_colors(colors, valid_colors, max_colors)
    for color in colors:
        print(f"Final color RGBA{color} ({color_percentages[color]:.2f}% of non-ignored pixels)")
    return colors

def create_color_images(colors, size=(32, 32)):
    images = []
    for color in colors:
        img = Image.new('RGBA', size, color)
        images.append(img)
    return images

def output_images(images, output_path):
    os.makedirs(output_path, exist_ok=True)
    for i, image in enumerate(images):
        image.save(os.path.join(output_path, f"{i}.png"))
        print(f"Saved color {i}: RGBA{image.getpixel((0, 0))}")

def main():
    PALETTE_PATH = ""
    OUTPUT_PATH = ""

    # The difference required to determine whether a colour is distinct or similar enough to be considered identical and not regarded as unique
    AVERAGE_DIFFERENCE_THRESHOLD = 10

    # The maximum number of colours to add in your palette. If it exceeds this amount, similar colours will be removed until the number of colours is equal to the limit.
    MAX_COLORS = 10
  
    # The minimum amount of percentage of the image a colour should occupy. Ignored colours are not counted in the total number of pixels when making this calculation.
    MIN_PIXEL_PERCENTAGE = 1.0
    
    # The list of colours to ignore completely. Transparent, white, and black have already been included.
    IGNORE_COLORS = [
        (0, 0, 0, 0),
        (0, 0, 0, 255),
        (255, 255, 255, 255)
    ]

    try:
        palette_image = Image.open(PALETTE_PATH)
        if palette_image.mode != 'RGBA':
            palette_image = palette_image.convert('RGBA')
        unique_colors = get_unique_colors(
            palette_image,
            avg_difference_threshold=AVERAGE_DIFFERENCE_THRESHOLD,
            max_colors=MAX_COLORS,
            min_pixel_percentage=MIN_PIXEL_PERCENTAGE,
            ignore_colors=IGNORE_COLORS
        )
        print(f"\nSummary:")
        print(f"- Final color count: {len(unique_colors)}")
        print(f"- Color difference threshold: {AVERAGE_DIFFERENCE_THRESHOLD}")
        print(f"- Minimum pixel percentage: {MIN_PIXEL_PERCENTAGE}% of non-ignored pixels")
        print(f"- Maximum colors: {MAX_COLORS}")
        print(f"- Ignored colors in list: {len(IGNORE_COLORS)}")
        color_images = create_color_images(unique_colors)
        print("\nSaving color swatches:")
        output_images(color_images, OUTPUT_TEXTURE_PATH)
    except FileNotFoundError:
        print(f"Error: Could not find palette file at {PALETTE_PATH}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
