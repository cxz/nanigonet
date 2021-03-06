import json
import os
import random
import sys
from pathlib import Path

from nanigonet.language_info import LanguageInfo

TRAIN_DIR = Path('data/train')


def main():
    random.seed(0)

    # First, read all the combined files per language ...
    lines_and_langs = []
    for info in LanguageInfo.values():
        print(f"Combining training data for {info['id']} ...", file=sys.stderr)

        if info['type'] == 'h':
            target_dir = TRAIN_DIR / info['id']
        else:
            target_dir = TRAIN_DIR / f"p-{info['id']}"

        if not os.path.exists(target_dir):
            print(f"Directory for {info['id']} does not exist. Skipping.", file=sys.stderr)
            continue

        combined_path = target_dir / 'combined.txt'
        if os.path.exists(combined_path):
            with open(combined_path) as f:
                for line in f:
                    text = line.strip()
                    text = text + ' '  # add a whitespace to account for punctuation.
                    lines_and_langs.append((text, f"{info['type']}:{info['id']}"))
        else:
            print(f"The combined.txt file for for {info['id']} does not exist.", file=sys.stderr)
            assert False

    # Second, shuffle them
    random.shuffle(lines_and_langs)

    # Third, split them into chunks
    last_split_i = 0
    last_split_j = 0
    dataset = []
    for i, (line, lang) in enumerate(lines_and_langs):
        for j in range(len(line) + 1):
            # split at position j means to split the text BEFORE text[j]
            if random.random() >= 0.01:
                continue

            # make a split at [i, j]
            if last_split_i == i:
                text = line[last_split_j:j]
                labels = [lang] * (j - last_split_j)
            else:
                text = ''
                labels = []
                for k in range(last_split_i, i+1):
                    if k == last_split_i:
                        partial_line, partial_lang = lines_and_langs[last_split_i]
                        partial_line = partial_line[last_split_j:]
                    elif k == i:
                        partial_line, partial_lang = line[:j], lang
                    else:
                        partial_line, partial_lang = lines_and_langs[k]

                    text += partial_line
                    labels.extend([partial_lang] * len(partial_line))

            assert len(text) == len(labels)
            if text:
                dataset.append((text, labels))

            last_split_i = i
            last_split_j = j

    # Fourth, add priority instances
    weight = 5
    with open(TRAIN_DIR / 'priority.txt') as f:
        for line in f:
            label, text = line[:-1].split(',', maxsplit=1)
            labels = [label] * len(text)
            for _ in range(weight):
                dataset.append((text, labels))

    # Finally, print out the results
    for text, labels in dataset:
        data = {
            'text': text,
            'labels': labels
        }
        print(json.dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    main()
