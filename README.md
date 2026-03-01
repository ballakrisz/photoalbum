# PhotoAlbum – OpenShift Deployment

Created by: Balla Krisztián (RZWVC0)
## Overview

PhotoAlbum is a Django web application deployed on OpenShift.

Users can:
- Register and log in
- Upload photos
- View uploaded photos

The application uses PostgreSQL for structured data and Persistent Volumes to ensure data survives pod restarts.

---

# Architecture

The system consists of:

- 1 Django application pod (`photoalbum-git`)
- 1 PostgreSQL pod (`postgres`)
- 2 Persistent Volume Claims (PVCs)
- 1 Service + 1 Route for external access

The application pod is stateless.
All important data is stored in persistent volumes.

---

# Components

## 1. Django Application (photoalbum-git)

- Type: Deployment
- Port: 8080
- Replicas: 1

### Responsibilities
- Handles HTTP requests
- Authentication
- Image upload
- Reads/writes data to PostgreSQL

### Persistent Storage
Mounted PVC: media-files-pvc → /opt/app-root/src/media

This stores uploaded image files.

If the pod restarts, images remain because they are stored in the PVC.

---

## 2. PostgreSQL Database (postgres)

- Type: Deployment
- Port: 5432
- Replicas: 1

### Responsibilities
- Stores users
- Stores image metadata
- Stores authentication data
- Stores Django migrations

### Persistent Storage
Mounted PVC: postgres-data-pvc → /var/lib/pgsql/data


This contains the full PostgreSQL data directory.

If the pod restarts, the database remains intact.

---

# Storage Design

Two separate PVCs are used:

### postgres-data-pvc
Used only by PostgreSQL.

Contains:
- Database tables
- WAL logs
- All relational data

### media-files-pvc
Used only by Django.

Contains:
- Uploaded image files

This separation follows proper Kubernetes design principles:
- Database storage is isolated
- Media storage is isolated
- Application remains stateless

---

# Networking Flow

User → OpenShift Route → Service → Django Pod → PostgreSQL Pod

- Route exposes the application externally
- Service connects traffic to the Django pod
- Django communicates with PostgreSQL internally

---

# Persistence Verification

The system was tested by:

- Deleting the PostgreSQL pod
- Deleting the Django pod

After recreation:
- Database data remained
- Uploaded images remained

This confirms correct persistent volume configuration.

---