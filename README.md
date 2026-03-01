# PhotoAlbum Application Architecture

## Overview

This application is deployed on OpenShift and consists of:

- A Django web application (`photoalbum-git`)
- A PostgreSQL database (`postgres`)
- Two Persistent Volume Claims (PVCs)
- A Service and Route for external access

The architecture follows proper Kubernetes separation of concerns:
- Database storage is isolated
- Media file storage is isolated
- Application is stateless

---

# Components

## 1️⃣ Django Application (photoalbum-git)

**Type:** Deployment  
**Replicas:** 1  
**Container Port:** 8080  

### Responsibilities

- Handles HTTP requests
- User authentication
- Image upload & display
- Database communication
- Stores uploaded image files

### Persistent Storage

Mounts:
