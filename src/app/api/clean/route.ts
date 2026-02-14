import { NextRequest, NextResponse } from 'next/server';
import { writeFile, readFile, unlink } from 'fs/promises';
import { join } from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import os from 'os';

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 });
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const tempDir = os.tmpdir();
    const inputFilePath = join(tempDir, `input-${Date.now()}-${file.name}`);
    const outputFilePath = join(tempDir, `output-${Date.now()}.csv`);

    await writeFile(inputFilePath, buffer);

    // Call the Python script
    // Assuming python is in the path. You might need to use 'python3' or full path depending on environment.
    // Also assuming src/script.py is relative to process.cwd()
    const scriptPath = join(process.cwd(), 'src/script.py');
    
    try {
      await execAsync(`python "${scriptPath}" "${inputFilePath}" "${outputFilePath}"`);
    } catch (error: any) {
      console.error('Python script error:', error);
       // Clean up input file if script fails
      try { await unlink(inputFilePath); } catch {}
      return NextResponse.json({ error: 'Failed to process file', details: error.message }, { status: 500 });
    }

    // Read the output file
    try {
        const outputBuffer = await readFile(outputFilePath);

        // Cleanup temp files
        await unlink(inputFilePath);
        await unlink(outputFilePath);

        return new NextResponse(outputBuffer, {
        headers: {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename="cleaned_data.csv"',
        },
        });
    } catch (readError) {
         console.error('Error reading output file:', readError);
         try { await unlink(inputFilePath); } catch {}
         return NextResponse.json({ error: 'Failed to read output file' }, { status: 500 });
    }

  } catch (error) {
    console.error('Upload handling error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
