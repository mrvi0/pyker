import React, { useState, useEffect } from 'react';
import { ProcessList } from './components/ProcessList';
import { ProcessForm } from './components/ProcessForm';
import { ScriptUpload } from './components/ScriptUpload';
import { Header } from './components/Header';
import { Process } from './types';

function App() {
  const [processes, setProcesses] = useState<Process[]>([]);
  const [scripts, setScripts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadProcesses();
    loadScripts();
    setupWebSocket();
  }, []);

  const setupWebSocket = () => {
    const websocket = new WebSocket(`ws://${window.location.host}/ws`);
    
    websocket.onopen = () => {
      console.log('WebSocket соединение установлено');
      websocket.send(JSON.stringify({ type: 'get_status' }));
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'status') {
        setProcesses(data.data);
      }
    };

    websocket.onclose = () => {
      console.log('WebSocket соединение закрыто');
      // Переподключение через 5 секунд
      setTimeout(setupWebSocket, 5000);
    };

    setWs(websocket);
  };

  const loadProcesses = async () => {
    try {
      const response = await fetch('/api/processes');
      const data = await response.json();
      setProcesses(data);
    } catch (error) {
      console.error('Ошибка загрузки процессов:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadScripts = async () => {
    try {
      const response = await fetch('/api/scripts');
      const data = await response.json();
      setScripts(data.scripts || []);
    } catch (error) {
      console.error('Ошибка загрузки скриптов:', error);
    }
  };

  const handleProcessAction = async (processId: string, action: string) => {
    try {
      const response = await fetch(`/api/processes/${processId}/${action}`, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Обновляем статус через WebSocket
        if (ws) {
          ws.send(JSON.stringify({ type: 'get_status' }));
        }
      } else {
        console.error(`Ошибка выполнения действия ${action}`);
      }
    } catch (error) {
      console.error(`Ошибка выполнения действия ${action}:`, error);
    }
  };

  const handleDeleteProcess = async (processId: string) => {
    if (window.confirm('Вы уверены, что хотите удалить этот процесс?')) {
      try {
        const response = await fetch(`/api/processes/${processId}`, {
          method: 'DELETE',
        });
        
        if (response.ok) {
          if (ws) {
            ws.send(JSON.stringify({ type: 'get_status' }));
          }
        }
      } catch (error) {
        console.error('Ошибка удаления процесса:', error);
      }
    }
  };

  const handleScriptUpload = () => {
    loadScripts();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Левая панель - Форма запуска и загрузка скриптов */}
            <div className="lg:col-span-1 space-y-6">
              <ProcessForm 
                scripts={scripts}
                onProcessStart={() => {
                  if (ws) ws.send(JSON.stringify({ type: 'get_status' }));
                }}
              />
              
              <ScriptUpload onUpload={handleScriptUpload} />
            </div>

            {/* Правая панель - Список процессов */}
            <div className="lg:col-span-2">
              <ProcessList
                processes={processes}
                loading={loading}
                onAction={handleProcessAction}
                onDelete={handleDeleteProcess}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 