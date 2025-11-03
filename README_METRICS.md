## Setting Up Test Documents

For real Azure API testing, you need accessible test documents. Here are your options:

### Option 1: Use a Public Test Document

Find a publicly accessible PDF or image URL (ensure you have permission to use it).

### Option 2: Upload to Azure Blob Storage (Recommended)

1. **Create Azure Storage Account**
   - Go to Azure Portal → Storage Accounts → Create
   - Create a blob container

2. **Upload a test document**
   - Upload a PDF or image file (e.g., `test.pdf`)

3. **Generate SAS URL**
   - Right-click file → Generate SAS
   - Set appropriate permissions and expiry
   - Copy the full URL with SAS token

4. **Example SAS URL:**
   ```
   https://yourstorage.blob.core.windows.net/test-container/test.pdf?sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2024-12-31T23:59:59Z&st=2024-01-01T00:00:00Z&spr=https&sig=your-signature
   ```

5. **Set as environment variable:**
   ```bash
   export TEST_DOCUMENT_URL="https://yourstorage.blob.core.windows.net/test-container/test.pdf?sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2024-12-31T23:59:59Z&st=2024-01-01T00:00:00Z&spr=https&sig=your-signature"
   ```

### Option 3: Use Azure Cognitive Services Sample Documents

Some Azure documentation provides sample documents you can use for testing.

## Important Notes

- **Cost**: Each API call costs based on pages processed
- **Rate Limits**: Azure has rate limits for API calls
- **File Types**: Supported formats include PDF, PNG, JPEG, BMP, TIFF
- **File Size**: Maximum 500 MB per document, 2000 pages for PDFs