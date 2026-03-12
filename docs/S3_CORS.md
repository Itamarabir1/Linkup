# S3 CORS Configuration for Direct Avatar Upload

When the frontend uploads avatars **directly to S3** using a presigned URL (PUT request from the browser), the S3 bucket must allow requests from the frontend origin. Otherwise the browser will block the request (CORS).

This is **configured in AWS** (Console, CLI, or IaC), not in application code.

## Required CORS rules

- **Allowed origins:** Your frontend origin(s), e.g.:
  - Development: `http://localhost:5173` (Vite default)
  - Production: `https://yourdomain.com`
- **Allowed methods:** `PUT`, `GET` (if you serve public read from the same bucket).
- **Allowed headers:** `Content-Type` (required for `PUT` with `Content-Type: image/webp`).

## Example CORS configuration (JSON)

Use this in AWS S3 → Bucket → Permissions → CORS, or via CLI/CloudFormation/Terraform.

```json
[
  {
    "AllowedHeaders": ["Content-Type", "Authorization"],
    "AllowedMethods": ["GET", "PUT", "HEAD"],
    "AllowedOrigins": [
      "http://localhost:5173",
      "http://127.0.0.1:5173",
      "https://your-production-domain.com"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3600
  }
]
```

Replace `https://your-production-domain.com` with your real frontend URL.

## AWS CLI example

```bash
# Save the JSON above to cors.json, then:
aws s3api put-bucket-cors --bucket YOUR_BUCKET_NAME --cors-configuration file://cors.json
```

## Verification

1. Open the app at `http://localhost:5173`, log in, and try uploading an avatar.
2. If CORS is missing or wrong, the browser console will show a CORS error and the PUT to the presigned URL will fail.
3. After adding the correct origin to `AllowedOrigins`, the upload should succeed.
