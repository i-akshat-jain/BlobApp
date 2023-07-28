import datetime
from django.shortcuts import render
from django.http import JsonResponse
from blobApp.models import Mention as m
from blobApp.models import Blob as b
import os
import pandas as pd
from datetime import date
import gzip
from io import BytesIO
from azure.storage.blob import BlobServiceClient as bs
from django.db.models import Q
import requests
from django.conf import settings


def get_data_and_save(blob_name):
    account_url = "https://invenicscasestudy.blob.core.windows.net/"
    container_name = "wiki"
    # clear all previous records form the mention and blob table
    m.objects.all().delete()
    # b.objects.all().delete()
    
    blob_name = blob_name+'.gz'
    try:
        # Get data from Azure Blob Storage and save to database
        blob_service_client = bs(account_url=account_url)
        container_client = blob_service_client.get_container_client(
            container_name)
        # Convert blob_list to a list to access the blobs
        blob_list = list(container_client.list_blobs())

        # blob_list = container_client.list_blobs()
        mention_id = 1
        idForBlobTable = 0
        x=1
        # blob_list = list(blob_list)
        for blob in blob_list:  
            if blob.name == blob_name:
                print(blob.name, idForBlobTable)

                blob_client = container_client.get_blob_client(blob)
                blob_contents = blob_client.download_blob()

                # Uncompress the data
                compressed_data = BytesIO(blob_contents.content_as_bytes())
                unzipped_data = gzip.GzipFile(fileobj=compressed_data).read()
                byte_file = BytesIO(unzipped_data)
                
                if b.objects.filter(blob=blob.name).exists():
                    print("object exists")
                else:
                    # idForBlobTable += 1
                    blob_obj = b.objects.create(id=idForBlobTable, blob=blob.name, date=date.today(), time = datetime.datetime.now().time())
                mentionObject = []
                rank = 1

                for line in byte_file:
                    fields = line.decode('utf-8').strip().split('\t')
                    if fields[0] == 'MENTION':
                        mention = fields[1]
                        position = fields[2]
                        wiki_url = fields[3]
                        mentionObject.append(
                            m(id=mention_id, blob_id=blob_obj, mention=mention, position=position,wikipedia_url=wiki_url))

                        # Create bulk insert having 3000 records each time
                        if rank % 3000 == 0:
                            m.objects.bulk_create(mentionObject)
                            print("Three thousand objects successfully put",
                                  rank, mention_id, idForBlobTable)
                            mentionObject = []

                        mention_id += 1
                        rank += 1

                # to save the last list of leftover objectsz
                m.objects.bulk_create(mentionObject)
        
            else:
                print("blob not found")
                idForBlobTable += 1

    except Exception as e:
        print(e)


    return True


def mention_list(request):
    mentions = m.objects.all()
    data = {
        'mentions': [
            {
                'mention': mention.mention,
                'position': mention.position,
                'wikipedia_url': mention.wikipedia_url,
                'blob_id': mention.blob_id.id,
            }
            for mention in mentions
        ]
    }
    return JsonResponse(data)



def home(request):
    context = {}
    if request.method == 'POST':
        blob_name = request.POST.get('blob_name')
        if blob_name:
            # Get the data and save to the database
            success = get_data_and_save(blob_name)
            if success:
                context['message'] = 'Data stored successfully!'
            else:
                context['message'] = 'Failed to get data from Azure.'

     # Make an HTTP GET request to the mention_list API
    try:
        response = requests.get('http://127.0.0.1:8000/api/mention/')
        data = response.json()
        mentions = data.get('mentions', [])
        context['mentions'] = mentions
    except requests.RequestException:
        context['message'] = 'Failed to fetch data from the API.'

    return render(request, 'blobApp/home.html', context)


    # # Fetch data from the local extracted file
    # extracted_file_path = os.path.join(settings.MEDIA_ROOT, f'{blob_name}.txt')
    # if os.path.exists(extracted_file_path):
    #     # File already exists, read the data from the file
    #     with open(extracted_file_path, 'r', encoding='utf-8') as f:
    #         encoded_data = f.read()
    # else:
    #     # File does not exist, download and extract from Azure Blob Storage
    #     download_url = f'{account_url}{container_name}/{blob_name}.gz'
    #     response = requests.get(download_url)
    #     if response.status_code == 200:
    #         # Save the downloaded .gz file to a temporary location
    #         temp_file_path = os.path.join(settings.MEDIA_ROOT, 'temp.gz')
    #         with open(temp_file_path, 'wb') as f:
    #             f.write(response.content)

    #         # Extract the .gz file
    #         with gzip.open(temp_file_path, 'rb') as gz_file, open(extracted_file_path, 'wb') as extracted_file:
    #             extracted_file.write(gz_file.read())

    #         # Delete the temporary .gz file
    #         os.remove(temp_file_path)

    #         # Read the data from the extracted file
    #         with open(extracted_file_path, 'r', encoding='utf-8') as f:
    #             encoded_data = f.read()

    # # Convert the data to a list of dictionaries
    # mentions = []
    # for line in encoded_data.splitlines():
    #     mention_parts = line.split('\t')
    #     if len(mention_parts) >= 3:
    #         mention_data = {
    #             'URL': mention_parts[0],
    #             'MENTION': mention_parts[1],
    #             'Wikipedia URL': mention_parts[2]
    #         }
    #         mentions.append(mention_data)

    # if mentions:
    #     # Save the data in PostgreSQL
    #     for mention_data in mentions:
    #         mention_object = m(
    #             mention=mention_data['MENTION'], url=mention_data['URL'], wikipedia_url=mention_data['Wikipedia URL'])
    #         mention_object.save()

    #     # Save the file in the media folder for future reference (if not already saved)
    #     if not os.path.exists(extracted_file_path):
    #         with open(extracted_file_path, 'w', encoding='utf-8') as f:
    #             for mention_data in mentions:
    #                 f.write(
    #                     f"{mention_data['URL']}\t{mention_data['MENTION']}\t{mention_data['Wikipedia URL']}\n")

    #     return True

    # return False


# @api_view(['GET', 'POST'])



