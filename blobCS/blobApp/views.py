import datetime
from django.shortcuts import render
from django.http import JsonResponse
from blobApp.models import Mention as m
from blobApp.models import Blob as b
# from blobApp.serializers import mentionSerializer as ser
# from blobApp.serializers import blobSerializer as bser
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.decorators import api_view
# from django_filters.rest_framework import filters
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
    account_url = "https://casestudy01.blob.core.windows.net/"
    container_name = "wikipedia"

    try:
        # Get data from Azure Blob Storage and save to database
        blob_service_client = bs(account_url=account_url)
        container_client = blob_service_client.get_container_client(
            container_name)
        blob_list = container_client.list_blobs()
        mention_id = 1
        idForBlobTable = 1

        for blob in blob_list:
            if blob.name == blob_name:
                print(blob.name, idForBlobTable)

                blob_client = container_client.get_blob_client(blob)
                blob_contents = blob_client.download_blob()

                # Uncompress the data
                compressed_data = BytesIO(blob_contents.content_as_bytes())
                unzipped_data = gzip.GzipFile(fileobj=compressed_data).read()
                f = BytesIO(unzipped_data)

                blob_obj = b.objects.create(
                    id=idForBlobTable, blob=blob.name, date=date.today())
                mentionObject = []
                rank = 1

                for line in f:
                    fields = line.decode('utf-8').strip().split('\t')
                    if fields[0] == 'MENTION':
                        mention = fields[1]
                        target_url = fields[2]
                        mentionObject.append(
                            m(id=mention_id, blob_id=blob_obj, rank=rank, mention=mention, url=target_url))

                        # Create bulk insert having 3000 records each time
                        if rank % 3000 == 0:
                            m.objects.bulk_create(mentionObject)
                            print("Three thousand objects successfully put",
                                  rank, mention_id, idForBlobTable)
                            mentionObject = []

                        mention_id += 1
                        rank += 1

                # to save the last list of leftover objects
                m.objects.bulk_create(mentionObject)
                idForBlobTable += 1

    except Exception as e:
        print(e)

    # Fetch data from the local extracted file
    extracted_file_path = os.path.join(settings.MEDIA_ROOT, f'{blob_name}.txt')
    if os.path.exists(extracted_file_path):
        # File already exists, read the data from the file
        with open(extracted_file_path, 'r', encoding='utf-8') as f:
            encoded_data = f.read()
    else:
        # File does not exist, download and extract from Azure Blob Storage
        download_url = f'{account_url}{container_name}/{blob_name}.gz'
        response = requests.get(download_url)
        if response.status_code == 200:
            # Save the downloaded .gz file to a temporary location
            temp_file_path = os.path.join(settings.MEDIA_ROOT, 'temp.gz')
            with open(temp_file_path, 'wb') as f:
                f.write(response.content)

            # Extract the .gz file
            with gzip.open(temp_file_path, 'rb') as gz_file, open(extracted_file_path, 'wb') as extracted_file:
                extracted_file.write(gz_file.read())

            # Delete the temporary .gz file
            os.remove(temp_file_path)

            # Read the data from the extracted file
            with open(extracted_file_path, 'r', encoding='utf-8') as f:
                encoded_data = f.read()

    # Convert the data to a list of dictionaries
    mentions = []
    for line in encoded_data.splitlines():
        mention_parts = line.split('\t')
        if len(mention_parts) >= 3:
            mention_data = {
                'URL': mention_parts[0],
                'MENTION': mention_parts[1],
                'Wikipedia URL': mention_parts[2]
            }
            mentions.append(mention_data)

    if mentions:
        # Save the data in PostgreSQL
        for mention_data in mentions:
            mention_object = m(
                mention=mention_data['MENTION'], url=mention_data['URL'], wikipedia_url=mention_data['Wikipedia URL'])
            mention_object.save()

        # Save the file in the media folder for future reference (if not already saved)
        if not os.path.exists(extracted_file_path):
            with open(extracted_file_path, 'w', encoding='utf-8') as f:
                for mention_data in mentions:
                    f.write(
                        f"{mention_data['URL']}\t{mention_data['MENTION']}\t{mention_data['Wikipedia URL']}\n")

        return True

    return False


# @api_view(['GET', 'POST'])
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

    return render(request, 'blobApp/home.html', context)



# def home(request):
#     context = {}
#     if request.method == 'POST':
#         blob_name = request.POST.get('blob_name')
#         if blob_name:
#             # Get the data from Azure
#             mentions = get_data_from_azure(blob_name)

#             if mentions:
#                 # Save the data in PostgreSQL
#                 for mention_data in mentions:
#                     mention_object = m(
#                         mention=mention_data['MENTION'], url=mention_data['URL'], wikipedia_url=mention_data['Wikipedia URL'])
#                     mention_object.save()

#                 # Save the file in the media folder for future reference (if not already saved)
#                 extracted_file_path = os.path.join(
#                     settings.MEDIA_ROOT, f'{blob_name}.txt')
#                 if not os.path.exists(extracted_file_path):
#                     with open(extracted_file_path, 'w', encoding='utf-8') as f:
#                         for mention_data in mentions:
#                             f.write(
#                                 f"{mention_data['URL']}\t{mention_data['MENTION']}\t{mention_data['Wikipedia URL']}\n")

#                 context['message'] = 'Data stored successfully!'
#             else:
#                 context['message'] = 'Failed to get data from Azure.'

#     return render(request, 'blobApp/home.html', context)
