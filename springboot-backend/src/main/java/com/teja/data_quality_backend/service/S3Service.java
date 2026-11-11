
package com.teja.data_quality_backend.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.CopyObjectRequest;
import java.io.IOException;
import java.nio.file.Path;

@Service
public class S3Service {

    private final S3Client s3Client;

    @Value("${aws.s3.bucket-name}")
    private String bucketName;

    public S3Service(S3Client s3Client) {
        this.s3Client = s3Client;
    }

    public String uploadRawFile(
            Path filePath,
            String batchId,
            String originalFileName
    ) throws IOException {

        // Prevent path manipulation through uploaded filenames.
        String safeFileName = Path.of(originalFileName)
                .getFileName()
                .toString();

        // Construct the S3 object key.
        String objectKey = "raw/" + batchId + "/" + safeFileName;

        // Prepare the S3 upload request.
        PutObjectRequest request = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .contentType("text/csv")
                .build();

        // Upload the file.
        s3Client.putObject(
                request,
                RequestBody.fromFile(filePath)
        );

        return objectKey;
    }

    public String copyToQuarantine(
            String sourceS3Key,
            String batchId,
            String runId,
            String originalFileName) {

        String safeFileName =
                Path.of(originalFileName).getFileName().toString();

        String quarantineKey =
                "quarantine/" + batchId + "/" + runId + "/" + safeFileName;

        CopyObjectRequest request = CopyObjectRequest.builder()
                .sourceBucket(bucketName)
                .sourceKey(sourceS3Key)
                .destinationBucket(bucketName)
                .destinationKey(quarantineKey)
                .build();

        s3Client.copyObject(request);

        return quarantineKey;
    }


    public String uploadCorrectedFile(
            Path filePath,
            String batchId,
            String runId,
            String originalFileName) throws IOException {

        String safeFileName =
                Path.of(originalFileName).getFileName().toString();

        String objectKey =
                "corrected/" + batchId + "/" + runId + "/" + safeFileName;

        PutObjectRequest request = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .contentType("text/csv")
                .build();

        s3Client.putObject(
                request,
                RequestBody.fromFile(filePath)
        );

        return objectKey;
    }

}
