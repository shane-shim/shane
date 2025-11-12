// Figma 플러그인 UI 표시
figma.showUI(__html__, { width: 300, height: 200 });

// UI로부터의 메시지 처리
figma.ui.onmessage = async (msg) => {
  console.log('Received message:', msg);

  if (msg.type === 'export-request') {
    try {
      const selection = figma.currentPage.selection;
      console.log('Selection:', selection.length, 'items');
      
      if (selection.length > 0) {
        for (const node of selection) {
          console.log('Processing node:', node.name, node.type);
          
          if (node.type === "FRAME" || node.type === "COMPONENT") {
            // Export image
            const bytes = await node.exportAsync({
              format: 'PNG',
              constraint: { type: 'SCALE', value: 2 }
            });
            
            console.log('Image exported, size:', bytes.length);
            
            // Convert to base64
            const base64Data = 'data:image/png;base64,' + Array.from(bytes)
              .map(byte => String.fromCharCode(byte))
              .join('');
            
            console.log('Base64 conversion complete');
            
            // Send to UI
            figma.ui.postMessage({
              type: 'export-image',
              data: {
                fileName: `${node.name}.png`,
                base64Data: base64Data
              }
            });
            
            // Extract design data
            const designData = {
              name: node.name,
              type: node.type,
              width: node.width,
              height: node.height,
              x: node.x,
              y: node.y,
              styles: {
                fills: node.fills,
                strokes: node.strokes,
                effects: node.effects
              }
            };
            
            console.log('Design data prepared');
            
            // Send design data
            figma.ui.postMessage({
              type: 'export-design',
              designData: designData
            });
            
            figma.ui.postMessage({
              type: 'status',
              message: 'Export complete!'
            });
          }
        }
      } else {
        figma.ui.postMessage({
          type: 'error',
          message: '프레임이나 컴포넌트를 선택해주세요.'
        });
      }
    } catch (error) {
      console.error('Export error:', error);
      figma.ui.postMessage({
        type: 'error',
        message: error.message
      });
    }
  }
};

// 사각형 생성 함수
async function createRectangle(data) {
  try {
    const rect = figma.createRectangle();
    rect.x = data.x || 0;
    rect.y = data.y || 0;
    rect.resize(data.width || 100, data.height || 100);

    if (data.fill) {
      rect.fills = [{
        type: 'SOLID',
        color: {
          r: data.fill.r || 0,
          g: data.fill.g || 0,
          b: data.fill.b || 0
        }
      }];
    }

    figma.currentPage.appendChild(rect);
    figma.viewport.scrollAndZoomIntoView([rect]);
    
    figma.ui.postMessage({
      type: 'rectangle-created',
      data: {
        id: rect.id,
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height
      }
    });
  } catch (error) {
    console.error('Error creating rectangle:', error);
    figma.ui.postMessage({
      type: 'error',
      message: 'Failed to create rectangle: ' + error.message
    });
  }
}

// 텍스트 생성 함수
async function createText(data) {
  try {
    const text = figma.createText();
    await figma.loadFontAsync({ family: "Inter", style: "Regular" });
    
    text.x = data.x || 0;
    text.y = data.y || 0;
    text.characters = data.content || '';
    
    if (data.fontSize) {
      text.fontSize = data.fontSize;
    }
    
    figma.currentPage.appendChild(text);
    figma.viewport.scrollAndZoomIntoView([text]);
    
    figma.ui.postMessage({
      type: 'text-created',
      data: {
        id: text.id,
        x: text.x,
        y: text.y,
        content: text.characters
      }
    });
  } catch (error) {
    console.error('Error creating text:', error);
    figma.ui.postMessage({
      type: 'error',
      message: 'Failed to create text: ' + error.message
    });
  }
} 