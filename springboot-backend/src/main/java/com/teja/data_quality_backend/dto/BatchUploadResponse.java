
package com.teja.data_quality_backend.dto;

public class BatchUploadResponse {

    private String batchId;
    private String message;
    private String fileName;
    private long fileSize;
    private String status;

    public BatchUploadResponse(
            String batchId,
            String message,
            String fileName,
            long fileSize,
            String status) {

        this.batchId = batchId;
        this.message = message;
        this.fileName = fileName;
        this.fileSize = fileSize;
        this.status = status;
    }

    public String getBatchId() {
        return batchId;
    }

    public String getMessage() {
        return message;
    }

    public String getFileName() {
        return fileName;
    }

    public long getFileSize() {
        return fileSize;
    }

    public String getStatus() {
        return status;
    }
}
