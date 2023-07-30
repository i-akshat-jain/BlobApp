# import datetime
# from django.shortcuts import render
# from django.http import JsonResponse
# from blobApp.models import Mention as m
# from blobApp.models import Blob as b
# import os
# import pandas as pd
# from datetime import date
# import gzip
# from io import BytesIO
# from azure.storage.blob import BlobServiceClient as bs
# from django.db.models import Q
# import requests
# from django.conf import settings
# import threading

# account_url = "https://invenicscasestudy.blob.core.windows.net/"
# container_name = "wiki"


# def get_data_and_save(blob_name):

#     # clear all previous records form the mention and blob table
#     m.objects.all().delete()
#     # b.objects.all().delete()

#     blob_name = blob_name+'.gz'
#     try:
#         # Get data from Azure Blob Storage and save to database
#         blob_service_client = bs(account_url=account_url)
#         container_client = blob_service_client.get_container_client(
#             container_name)
#         # Convert blob_list to a list to access the blobs
#         blob_list = list(container_client.list_blobs())

#         # blob_list = container_client.list_blobs()
#         mention_id = 1
#         idForBlobTable = 0
#         # blob_list = list(blob_list)
#         for blob in blob_list:
#             if blob.name == blob_name:
#                 print(blob.name, idForBlobTable)
#                 global found_blob
#                 found_blob = blob
#                 blob_client = container_client.get_blob_client(blob)
#                 blob_contents = blob_client.download_blob()

#                 # Uncompress the data
#                 compressed_data = BytesIO(blob_contents.content_as_bytes())
#                 unzipped_data = gzip.GzipFile(fileobj=compressed_data).read()
#                 # Set a range to read the compressed data to just 3000 lines
#                 unzipped_range_data = unzipped_data[:100000]

#                 byte_file = BytesIO(unzipped_range_data)

#                 if b.objects.filter(blob=blob.name).exists():
#                     print("object exists")
#                 else:
#                     # idForBlobTable += 1
#                     global blob_obj
#                     blob_obj = b.objects.create(id=idForBlobTable, blob=blob.name, date=date.today(
#                     ), time=datetime.datetime.now().time())
#                 mentionObject = []
#                 rank = 1

#                 for line in byte_file:
#                     fields = line.decode('utf-8').strip().split('\t')
#                     if fields[0] == 'MENTION':
#                         mention = fields[1]
#                         position = fields[2]
#                         wiki_url = fields[3]
#                         mentionObject.append(
#                             m(id=mention_id, blob_id=blob_obj, mention=mention, position=position, wikipedia_url=wiki_url))

#                         # Create bulk insert having 3000 records each time
#                         if rank % 500 == 0:
#                             # Save the first 2000 mentions to the database
#                             m.objects.bulk_create(mentionObject)
#                             mentionObject = []
#                             # Load the remaining mentions in the background
#                             print("five objects successfully put",
#                                   rank, mention_id, idForBlobTable)
#                             threading.Thread(target=load_remaining_mentions, args=(
#                                 found_blob, mention_id, container_client, blob_obj)).start()
#                         mention_id += 1
#                         rank += 1

#                 # to save the last list of leftover objectsz
#                 if mentionObject:
#                     m.objects.bulk_create(mentionObject)

#             else:
#                 print("blob not found")
#                 idForBlobTable += 1

#     except Exception as e:
#         print(e)

#     return True


# def load_remaining_mentions(blob_name, mention_id, container_client, blob_obj):
#     # account_url = "https://invenicscasestudy.blob.core.windows.net/"
#     # container_name = "wiki"
#     # Load the remaining mentions in the background
#     blob_client = container_client.get_blob_client(blob_name)
#     blob_contents = blob_client.download_blob()

#     # Uncompress the data
#     compressed_data = BytesIO(blob_contents.content_as_bytes())
#     unzipped_data = gzip.GzipFile(fileobj=compressed_data).read()

#     # Read the remaining data from the compressed file
#     remaining_data = unzipped_data[100000:]

#     remaining_byte_file = BytesIO(remaining_data)
#     # Create a list of mention objects from the remaining data
#     mentionObject = []
#     mention_id = mention_id+1
#     rank = 1
#     for line in remaining_byte_file:
#         fields = line.decode('utf-8').strip().split('\t')
#         if fields[0] == 'MENTION':
#             mention = fields[1]
#             position = fields[2]
#             wiki_url = fields[3]
#             mentionObject.append(
#                 m(id=mention_id, blob_id=blob_obj, mention=mention, position=position, wikipedia_url=wiki_url))
#             print("five objects successfully put",
#                   mention_id, rank)
#             # Create bulk insert having 3000 records each time
#             if rank % 5000 == 0:
#                 # Save the first 2000 mentions to the database
#                 m.objects.bulk_create(mentionObject)
#                 mentionObject = []
#                 # Load the remaining mentions in the background
#                 print("five objects successfully put",
#                       rank, mention_id, idForBlobTable)

#             mention_id += 1
#             rank += 1

#     # to save the last list of leftover objectsz
#     if mentionObject:
#         m.objects.bulk_create(mentionObject)


# def mention_list(request):
#     mentions = m.objects.all()
#     data = {
#         'mentions': [
#             {
#                 'mention': mention.mention,
#                 'position': mention.position,
#                 'wikipedia_url': mention.wikipedia_url,
#                 'blob_id': mention.blob_id.id,
#             }
#             for mention in mentions
#         ]
#     }
#     return JsonResponse(data)


# def home(request):
#     context = {}
#     if request.method == 'POST':
#         blob_name = request.POST.get('blob_name')
#         if blob_name:
#             # Get the data and save to the database
#             success = get_data_and_save(blob_name)
#             if success:
#                 context['message'] = 'Data stored successfully!'
#             else:
#                 context['message'] = 'Failed to get data from Azure.'

#      # Make an HTTP GET request to the mention_list API
#     try:
#         response = requests.get('http://127.0.0.1:8000/api/mention/')
#         data = response.json()
#         mentions = data.get('mentions', [])
#         context['mentions'] = mentions
#     except requests.RequestException:
#         context['message'] = 'Failed to fetch data from the API.'

#     return render(request, 'blobApp/home.html', context)
# {% comment %} <!DOCTYPE html>
# <html>
# <head>
#     <title>Invenics Case Study</title>
# </head>
# <body>
#     <div class="container">
#         <h1>Invenics Case Study</h1>
#             <p>The objective of this case study is to understand your approach and capabilities to deal with large data sets. The case study is based on a hypothetical company and public data sources but aims to replicate some of the common challenges in the field of data engineering.</p>
#             <p>A technology and media company has engaged Invenics to assist in building a Big Data solution. The company aims to build a product to capture information about the digital footprint of target web URLs. Specifically, the company has developed web crawlers that captures information of all mentions of a particular website and saves it in a database. As a prototype, they have run webcrawlers to extract information of all websites that have at least one hyperlink pointing into English Wikipedia. The dataset is in this format for each record and repeats for all URL’s identified through the scan. Pages are separated from each other by two blank lines.</p>
#             <p>Please try to produce the most optimized solution that you can. The UI should be responsive and feel free to produce an UI that reflects your design skillset.</p>

#             <form method="post" action="{% url 'home' %}">
#                 {% csrf_token %}
#                 <label for="blob_name">Enter Blob Name:</label>
#                 <input type="text" name="blob_name" id="blob_name" required>
#                 <button type="submit">Submit</button>
#             </form>

#             {% comment %} <input type="text" id="search" placeholder="Search"> {% endcomment %}
#         <table id="results">
#         </table>
#         {% comment %} <script src="script.js"></script> {% endcomment %}
# </div>

#     {% if message %}
#         <div class="alert alert-success">
#             {{ message }}
#         </div>
#     {% endif %}

#     {% if mentions %}
#         <table>
#             <thead>
#                 <tr>
#                     <th>Mention</th>
#                     <th>Position</th>
#                     <th>Wikipedia URL</th>

#                 </tr>
#             </thead>
#             <tbody>
#                 {% for mention in mentions %}
#                     <tr>
#                         <td>{{ mention.mention }}</td>
#                         <td>{{ mention.position }}</td>
#                         <td>{{ mention.wikipedia_url }}</td>
#                     </tr>
#                 {% endfor %}
#             </tbody>
#         </table>
#         {% if page.has_next %}
#             <button class="load-more-btn" id="load-more-btn">Load More</button>
#         {% endif %}

#         <script>
# document.addEventListener("DOMContentLoaded", function() {
#     const tableBody = document.querySelector("tbody");
#     const loadMoreBtn = document.querySelector("#load-more-btn");
#     let page = 2;

#     function fetchMoreMentions() {
#         fetch(`http://127.0.0.1:8000/api/mention/?page=${page}`)
#             .then(response => response.json())
#             .then(data => {
#                 const mentions = data.mentions;
#                 const has_next_page = data.has_next_page;
                
#                 mentions.forEach(mention => {
#                     const newRow = document.createElement("tr");
#                     newRow.innerHTML = `
#                         <td>${mention.mention}</td>
#                         <td>${mention.position}</td>
#                         <td>${mention.wikipedia_url}</td>
#                         <td>${mention.blob_id}</td>
#                     `;
#                     tableBody.appendChild(newRow);
#                 });

#                 if (has_next_page) {
#                     page++;
#                 } else {
#                     loadMoreBtn.style.display = "none";
#                 }

#                 const previousPageBtn = document.createElement("button");
#                 previousPageBtn.innerHTML = "Previous";
#                 previousPageBtn.addEventListener("click", function() {
#                     page--;
#                     fetchMoreMentions();
#                 });

#                 const nextPageBtn = document.createElement("button");
#                 nextPageBtn.innerHTML = "Next";
#                 nextPageBtn.addEventListener("click", function() {
#                     page++;
#                     fetchMoreMentions();
#                 });

#                 document.body.appendChild(previousPageBtn);
#                 document.body.appendChild(nextPageBtn);
#             })
#             .catch(error => console.error(error));
#     }

#     loadMoreBtn.addEventListener("click", fetchMoreMentions);
# });
# </script>

#     {% else %}
#         <p>No mentions available.</p>
#     {% endif %}
# </body>
# </html> {% endcomment %}