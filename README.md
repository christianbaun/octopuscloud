# octopuscloud

The [Octopus Cloud Storage System](http://cloudoctopus.appspot.com/) is a software service, designed to provide a high-availability cloud-based storage solution.

Several different S3-compatible public and private cloud storage services exist:

- [Amazon S3](http://aws.amazon.com/s3/)
- Google Storage
- Connectria Cloud Storage
- Host Europe Cloud Storage
- Walrus (Eucalyptus)
- Cumulus (Nimbus)
- Swift (OpenStack)
- Cloud Storage

Octopus' aim is to support all available S3-compatible services. Support for S3 and Walrus is implemented now.

The software is still under development. See the list of already implemented features.

**Web site of Octopus:** [http://cloudoctopus.appspot.com](http://cloudoctopus.appspot.com)

# How it works

The paper **Redundant Cloud Storage with Octopus** from August 2011 summarizes the features and design of Octopus.

Octopus is designed to run inside a PaaS like Google’s App Engine, AppScale or typhoonAE. One of the benefits of a cloud platform is that the users don’t need to install the software at client side. A drawback is that the files that shall be uploaded to the cloud storage services cannot be cached by Octopus itself because files cannot be stored by the applications inside the PaaS. This causes another drawback of Octopus. All files need to be transferred to each connected storage service. If a user has credentials for three storage services, the file needs to be transferred from the client (browser) to the storage services one after one.

Users can import their credentials to S3 and Walrus services into Octopus. The software checks if a bucket octopus_storage-at-<username> exists. If not, the bucket will be created. The users can upload files - called objects in the S3 world – with one click to the connected storage services into the Octopus bucket.

S3 and Walrus both store a MD5 checksum for each object. These checksums are transferred automatically when a list of all objects is requested and they allow checking if the objects located at the different storage services are synchronized.

Everytime, a list of objects is requested, Octopus checks if the data is still synchronized across the storage services. Users can erase objects and alter the Access Control List (ACL) of each object.

Octopus is written in Python and JavaScript. The communication with the S3-compatible storage services is done via boto, a Python interface to the Amazon Web Services. The user interface is HTML (generated with Django) and some JavaScript (jQuery).

# Implemented Features

- Import of credentials for Amazon S3 and Walrus.
- RAID-1 mode. Upload to one or two storage services with a single click.
- Check for synchronicity with help of the MD5 checksums.
- Erase objects inside different storage services with a single click.
- Erase all objects in all storage services with a single click.
- Alter Access Control List (ACL) of objects inside one or two storage services with a single click.

# Next Steps

- Implementation of automatic repair when check for synchronicity failed.
- Currently, each user can import credentials for only one Amazon S3 account and a single Walrus Private Cloud storage service.
- Implement support for Google Blobstore. Objects (called blobs) of max. 2 GB size can be upload into the Blobstore via HTTP POST and then accessed from App Engine applications. Blobstore could be used as a proxy for Octopus to avoid multiple uploads from the browser to the storage services.
- Google Storage could be used as a proxy for Octopus too because objects inside Google Storage can be accessed from applications running inside the App Engine.
- Implementation of a RAID-5 mode. Benefits would be that no provider has a full (working) copy of the customers data and if a provider is not operational any more, the customers data is still available.

# Challanges and Limitations

- Cumulus does not support uploading objects via POST yet. Maybe future releases have this feature and can be used by Octopus.
- In S3 and Google Storage, the MD5 checksums is enclosed by double quotes. In Walrus they are not.
- If no submit button inside a form is used to upload an object into Walrus, some bytes of garbage data is appended to the object.
