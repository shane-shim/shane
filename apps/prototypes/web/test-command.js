const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:3055');

ws.on('open', function open() {
  // 사각형 생성 명령 전송
  const command = {
    type: 'create-rectangle',
    data: {
      x: 100,
      y: 100,
      width: 200,
      height: 100,
      fill: {r: 1, g: 0, b: 0}  // 빨간색 사각형
    }
  };

  ws.send(JSON.stringify(command));
  console.log('Rectangle creation command sent!');
}); 