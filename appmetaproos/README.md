# Alessio Photography - Facial Recognition Photo Portal

A secure web application that allows photographer Alessio to upload photos and clients to access their personalized galleries using facial recognition technology.

## Features

1. **Admin Panel**: Upload multiple photos that get automatically indexed for facial recognition
2. **Facial Recognition Login**: Clients take a selfie to access their personalized photo gallery
3. **Secure Storage**: Photos stored in Amazon S3 with facial data in SQLite database
4. **Responsive Design**: Works on desktop and mobile devices

## Technology Stack

- **Backend**: Python with Flask
- **Cloud Services**: Amazon S3 for storage, Amazon Rekognition for facial recognition
- **Database**: SQLite for storing face-to-photo mappings
- **Frontend**: HTML, CSS (Bootstrap 5), JavaScript (getUserMedia API)

## Prerequisites

Before running this application, you need:

1. An AWS account with:
   - IAM user credentials (access key ID and secret access key)
   - Two S3 buckets:
     - One for storing gallery photos
     - One for temporary selfies
   - An Amazon Rekognition Face Collection

2. Python 3.7 or higher installed

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd alessio-photography
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure AWS Settings

Set the following environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_aws_access_key_id
export AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
export AWS_REGION=your_aws_region  # e.g., us-east-1
export S3_GALLERY_BUCKET=your_gallery_bucket_name
export S3_SELFIE_BUCKET=your_selfie_bucket_name
export REKOGNITION_COLLECTION_ID=your_collection_id
```

Alternatively, you can modify the values in `config.py` directly (not recommended for production).

### 4. Initialize the Database

The database will be automatically created when you first run the application.

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Admin Panel

1. Navigate to `http://localhost:5000/admin`
2. Select multiple photos to upload
3. The system will:
   - Upload photos to the S3 gallery bucket
   - Index faces in each photo using Amazon Rekognition
   - Store face-to-photo mappings in the database

### Client Portal

1. Navigate to `http://localhost:5000`
2. Allow camera access when prompted
3. Position your face within the circle
4. Click "Take Selfie"
5. The system will:
   - Upload your selfie to the S3 selfie bucket
   - Search for matching faces using Amazon Rekognition
   - Retrieve your personalized photos from the database
   - Display your photo gallery

## Security Considerations

- In production, change the Flask secret key in `app.py`
- Use environment variables for AWS credentials instead of hardcoding them
- Implement proper authentication for the admin panel
- Consider adding rate limiting to prevent abuse
- Ensure HTTPS is used in production

## Project Structure

```
.
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── database.py            # Database operations
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── faces.db               # SQLite database (created automatically)
├── temp/                  # Temporary directory for file processing
├── templates/
│   ├── admin.html         # Admin panel template
│   ├── index.html         # Client portal template
│   └── gallery.html       # Photo gallery template
└── static/
    └── js/
        └── camera.js      # Client-side camera functionality
```

## Troubleshooting

### Camera Access Issues

- Ensure you're accessing the application over HTTPS in production (getUserMedia requires secure context)
- Check browser permissions for camera access
- Try a different browser if issues persist

### AWS Configuration Issues

- Verify your AWS credentials are correct
- Ensure your IAM user has permissions for S3 and Rekognition
- Confirm your S3 bucket names and Rekognition collection ID are correct

### Facial Recognition Issues

- Ensure good lighting when taking selfies
- Make sure your face is clearly visible in both the gallery photos and selfie
- Try uploading higher quality photos for better face detection

## License

This project is licensed under the MIT License - see the LICENSE file for details.