# PhotoAlbum – OpenShift Deployment

Created by: **Balla Krisztián (RZWVC0)**

The application is available at:  
https://photoalbum-git-skicpausz-dev.apps.rm1.0a51.p1.openshiftapps.com/

*(If the application is temporarily unavailable, the Developer Sandbox may stop idle pods. Please contact me on Teams and I will restart them.)*

![App Overview](docs/app_overview.png)

---

# Overview

PhotoAlbum is a Django web application deployed on OpenShift.

Users can:

- Register and log in
- Upload photos
- View uploaded photos
- Delete their own photos

The application uses:

- **PostgreSQL** for relational data
- **AWS S3 object storage** for uploaded images
- **OpenShift Deployments and Services** for orchestration

The system is designed to be **stateless and scalable**.

---

# Architecture

The system consists of:

- 1 Django application pod (`photoalbum-git`)
- 1 PostgreSQL pod (`postgres`)
- 1 Persistent Volume Claim (PVC) for PostgreSQL
- AWS S3 bucket for image storage
- 1 Service + 1 Route for external access

The Django application pod is completely **stateless**.

All persistent data is stored externally:

- Relational data → PostgreSQL PVC  
- Image files → AWS S3  

![Pod Architecture](docs/pod_arch.png)

---

# Components

## 1. Django Application (`photoalbum-git`)

- Type: Deployment
- Port: 8080
- Replicas: 1 (scalable)
- Stateless

### Responsibilities

- Handles HTTP requests
- User authentication
- Image upload
- Stores metadata in PostgreSQL
- Uploads image files directly to AWS S3

### Storage

No Persistent Volume is mounted.

Uploaded images are stored in AWS S3: `photoalbum-skicpausz-media`

---

## 2. PostgreSQL Database (`postgres`)

- Type: Deployment
- Port: 5432
- Replicas: 1
- Stateful

### Responsibilities

- Stores users
- Stores image metadata
- Stores authentication data
- Stores Django migrations

### Persistent Storage

Mounted PVC: `postgres-data-pvc → /var/lib/pgsql/data`

If the PostgreSQL pod restarts, the database remains intact.

---

# Storage Design

## postgres-data-pvc

Used only by PostgreSQL.

Contains:

- Database tables
- WAL logs
- All relational data

![Postgres PVC](docs/postgresql_pvc.png)

## AWS S3 Object Storage

Used only by the Django application.

Contains:

- Uploaded image files

![S3 storage](docs/S3_bucket.png)

Accessed by OpenShift through the `photoalbum-django` **IAM user**.

![IAM user](docs/iam_user.png)
---
# Functionalities

The application staiesfies the minimal functional requirements:
- Photo upload/delete
- Photos have a name (max 40 characters) and an upload date
- Photos can be sorted by their name and the upload date
- When clicked on an item in the album its photo is displayed
- User handling: register, login, logout
- Upload and delete allowed only for authenticated users

Additional functionalities:
- The galery is displayed as a tile of images, where instead of the names of the entries, the user can see a preview of the image associated with that entry
- Photos can be only deleted by the user who uploaded them
- An admin user was created (me), who can delete any images

---
# Why S3 Instead of PVC for Media Files?

Initially, uploaded images were stored on a shared Persistent Volume (PVC), and under normal circumstances this setup worked as expected. However, during redeployments, an issue occurred intermittently — roughly 1 out of 5 times, the new pod failed to start while the old pod continued running.

After inspecting the **Events** tab of the newly created pod (which remained stuck in the *Creating* state), I discovered that the error was caused by the media PVC still being mounted to the old pod. The underlying problem was that the volume supported only **ReadWriteOnce (RWO)** access mode, meaning it could be attached to only one pod at a time.

Because the deployment strategy was set to **RollingUpdate**, Kubernetes attempted to start the new pod before terminating the old one. However, the new pod could not mount the PVC since it was still attached to the running old pod. At the same time, the old pod was not terminated because the RollingUpdate strategy ensures availability by keeping it alive until the new pod becomes ready. This resulted in a deadlock situation:

- The new pod could not start without the PVC.
- The PVC could not detach while the old pod was still running.
- The old pod would not terminate because the new pod never became ready.

The only way to resolve the situation manually was to delete the old pod, which would release the volume and allow the new pod to mount it successfully.

A simple solution would've been to switch the deployment strategy to **Recreate**, which termintes all running pods, before starting the new ones. But, as my future tasks include making my application **scalable**, this **RWO** PVC would prevent me from running multiple pods of my application. Thus, I decided to switch to an AWS S3 object storage as my media storage. 
## Why S3 Solves This Problem

Switching to S3 (object storage) eliminates this limitation entirely. Unlike PVCs with RWO access mode:

- S3 is not mounted as a block device.
- Multiple pods can access the same bucket simultaneously.
- There is no attachment/detachment lifecycle tied to individual pods.
- Rolling updates work seamlessly without storage-related conflicts.

By moving media files to S3, the deployment becomes more reliable, scalable, and resilient to rolling updates. It also improves decoupling between compute (pods) and storage, aligning better with cloud-native design principles.

---

# Persistence Verification (test for myself)

The system was tested by:

- Deleting the PostgreSQL pod
- Deleting the Django pod

After recreation:
- Database data remained (user info persisted thanks to the PVC)
- Uploaded images remained (media persisted thanks to the S3 object storage)

This confirmed correct persistent volume configuration.

---


# Auto-build based on git

This is mainly just for me, so if I have to do it again, i know how to.

According to the Red Hat tutorial: https://redhat-scholars.github.io/openshift-starter-guides/rhs-openshift-starter-guides/4.9/nationalparks-java-codechanges-github.html

1. Copy the webhook for github (with secret!)
![OpenShift hook](docs/OpenShift_webhook.png)

2. Paste it into github
![Pod Architecure](docs/github_webhook.png)


### Unfortunately it did not work.
I recieved the following response on github:
```bash
{"kind":"Status","apiVersion":"v1","metadata":{},"status":"Failure","message":"buildconfigs.build.openshift.io \"photoalbum-git\" is forbidden: User \"system:anonymous\" cannot create resource \"buildconfigs/webhooks\" in API group \"build.openshift.io\" in the namespace \"skicpausz-dev\"","reason":"Forbidden","details":{"name":"photoalbum-git","group":"build.openshift.io","kind":"buildconfigs"},"code":403}
```
According to a thread i found online (https://access.redhat.com/solutions/7105930):

"From OCP version 4.16 onward, all webhooks for BuildConfigs must either have an OpenShift authentication token in their HTTP headers, OR an administrator must grant the system:webhook role to the system:unauthenticated group in the namespace where the BuildConfig resides.
"

I had to add the webhook role to the unauthenticated group via the following command:
```bash
oc policy add-role-to-group system:webhook system:unauthenticated -n skicpausz-dev
```

### After this, the GitHub webhook response was 200 OK, but pushing still didn't initiate a build.

OpenShift defaults to the "master" branch of git, while I was using the "main" branch. To force OpenShift to use the "main" branch, i had to add the following code to my BuildConfig
```bash
source:
  type: Git
  git:
    uri: 'https://github.com/ballakrisz/photoalbum.git'
    ref: main
  contextDir: /
```
Also, I had to add this to the yaml config of my photoalbum project, to make sure the Deployment is watching the ImageStream and that every new build forces a new rollout of my pod (Though i tried like 10 things all at the same time, so this might not be necessary. I think the build automatically starts a new pod when finished by default):
```bash
metadata:
  annotations:
    image.openshift.io/triggers: '[{"from":{"kind":"ImageStreamTag","name":"photoalbum-git:latest"},"fieldPath":"spec.template.spec.containers[?(@.name==\"photoalbum-git\")].image"}]'
```

---

# Auto-scaling Configuration
To ensure the application can handle increasing load, **Horizontal Pod Autoscaling (HPA)** was configured in OpenShift.

The goal was to:
- Automatically **scale up** when CPU usage increases
- Automatically **scale down** when load decreases


## HPA Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: photoalbum-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: photoalbum-git
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      selectPolicy: Max
      policies:
        - type: Percent
          value: 100
          periodSeconds: 10
        - type: Pods
          value: 2
          periodSeconds: 10
    scaleDown:
      stabilizationWindowSeconds: 10
      selectPolicy: Max
      policies:
        - type: Percent
          value: 100
          periodSeconds: 10
```
S
