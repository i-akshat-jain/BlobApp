import csv


def parse_sample_text(sample_text):
    data = []
    lines = sample_text.split('\n\n')
    for line in lines:
        if line.strip():
            parts = line.split('\n')
            try:
                url_parts = parts[0].split('\t')
                mention_parts = parts[1].split('\t')
                if len(url_parts) >= 2 and len(mention_parts) >= 3:
                    url = url_parts[1]
                    mention = mention_parts[1]
                    wikipedia_url = mention_parts[2]
                    data.append({'URL': url, 'MENTION': mention,
                                'Wikipedia URL': wikipedia_url})
                else:
                    print(f"Invalid data format: {parts}")
            except IndexError as e:
                print(f"Error parsing line: {line}\n{e}")
    return data


def write_to_csv(data, output_file):
    with open(output_file, mode='w', newline='') as csv_file:
        fieldnames = ['URL', 'MENTION', 'Wikipedia URL']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


if __name__ == '__main__':
    with open('blobCS/media/data-00000-of-00010.txt', 'r', encoding='utf-8-sig') as file:
        sample_text = file.read()

    structured_data = parse_sample_text(sample_text)
    write_to_csv(structured_data, 'output.csv')

# import csv
# import re


# def read_txt_file(file_name):
#   with open(file_name, 'r', encoding='utf-8-sig') as f:
#     content = f.read()
#   return content


# def extract_mentions(content):
#   mentions = []
#   pattern = r'\[([^\]]+)\]'
#   matches = re.findall(pattern, content)
#   for match in matches:
#     mentions.append((match, match.replace('[', '').replace(']', '')))
#   return mentions


# def extract_tokens(content):
#   tokens = []
#   pattern = r'\w+'
#   matches = re.findall(pattern, content)
#   for match in matches:
#     tokens.append(match)
#   return tokens


# def write_to_csv(mentions, tokens, file_name):
#   with open(file_name, 'w', newline='') as f:
#     writer = csv.writer(f)
#     writer.writerow(['Mention', 'URL', 'Tokens'])
#     for mention, url in mentions:
#       writer.writerow([mention, url, ', '.join(tokens)])


# if __name__ == '__main__':
#   content = read_txt_file('blobCS/media/data-00000-of-00010.txt')
#   mentions = extract_mentions(content)
#   tokens = extract_tokens(content)
#   write_to_csv(mentions, tokens, 'output.csv')
