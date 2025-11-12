import { writeFile, mkdir } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 필요한 디렉토리 생성
async function ensureDirectoryExists(dirPath) {
  try {
    await mkdir(dirPath, { recursive: true });
    console.log(`Directory created: ${dirPath}`);
  } catch (error) {
    if (error.code !== 'EEXIST') {
      throw error;
    }
  }
}

const server = Bun.serve({
  port: 3055,
  fetch(req, server) {
    // Upgrade the request to a WebSocket connection
    if (server.upgrade(req)) {
      return; // Return if upgrade was successful
    }
    return new Response('WebSocket server is running');
  },
  websocket: {
    open(ws) {
      console.log('New client connected!');
      // 초기 연결 확인 메시지 전송
      ws.send(JSON.stringify({ 
        type: 'connected',
        message: 'Successfully connected to server'
      }));
    },
    async message(ws, data) {
      try {
        const message = JSON.parse(data.toString());
        console.log('Received message type:', message.type);

        if (message.type === 'export-image') {
          console.log('Processing image export...');
          const { fileName, base64Data } = message.data;
          
          // 이미지 디렉토리 생성
          const imageDir = join(__dirname, '../../public/images');
          await ensureDirectoryExists(imageDir);
          
          // base64 데이터에서 실제 이미지 데이터만 추출
          const base64Image = base64Data.split(',')[1];
          const imageBuffer = Buffer.from(base64Image, 'base64');
          
          const imagePath = join(imageDir, fileName);
          await writeFile(imagePath, imageBuffer);
          console.log(`Image saved: ${imagePath}`);
          
          ws.send(JSON.stringify({
            type: 'image-saved',
            data: { fileName, path: imagePath }
          }));
        }

        if (message.type === 'export-design') {
          console.log('Processing design export...');
          const { designData } = message;
          
          // 디자인 데이터 디렉토리 생성
          const dataDir = join(__dirname, '../../src/data');
          await ensureDirectoryExists(dataDir);
          
          const designPath = join(dataDir, 'design-data.json');
          await writeFile(designPath, JSON.stringify(designData, null, 2));
          console.log(`Design data saved: ${designPath}`);
          
          ws.send(JSON.stringify({
            type: 'design-saved',
            data: { path: designPath }
          }));
        }
      } catch (error) {
        console.error('Error processing message:', error);
        ws.send(JSON.stringify({
          type: 'error',
          error: error.message
        }));
      }
    },
    close(ws) {
      console.log('Client disconnected');
    },
    error(ws, error) {
      console.error('WebSocket error:', error);
    }
  }
});

console.log(`WebSocket server started on port ${server.port}`); 