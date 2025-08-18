import React, { useState } from 'react';
import { Process } from '../types';

interface ProcessListProps {
  processes: Process[];
  loading: boolean;
  onAction: (processId: string, action: string) => void;
  onDelete: (processId: string) => void;
}

export const ProcessList: React.FC<ProcessListProps> = ({ 
  processes, 
  loading, 
  onAction, 
  onDelete 
}) => {
  const [selectedProcess, setSelectedProcess] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800';
      case 'stopped':
        return 'bg-gray-100 text-gray-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'starting':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return 'Запущен';
      case 'stopped':
        return 'Остановлен';
      case 'error':
        return 'Ошибка';
      case 'starting':
        return 'Запуск';
      default:
        return status;
    }
  };

  const loadLogs = async (processId: string) => {
    setLoadingLogs(true);
    try {
      const response = await fetch(`/api/processes/${processId}/logs?limit=100`);
      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки логов:', error);
    } finally {
      setLoadingLogs(false);
    }
  };

  const handleShowLogs = (processId: string) => {
    if (selectedProcess === processId) {
      setSelectedProcess(null);
      setLogs([]);
    } else {
      setSelectedProcess(processId);
      loadLogs(processId);
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-center items-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">
          Процессы ({processes.length})
        </h2>
      </div>
      
      {processes.length === 0 ? (
        <div className="p-6 text-center text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-2">Нет запущенных процессов</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-200">
          {processes.map((process) => (
            <div key={process.id} className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-lg font-medium text-gray-900">
                      {process.name}
                    </h3>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(process.status)}`}>
                      {getStatusText(process.status)}
                    </span>
                    {process.auto_restart && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        Автоперезапуск
                      </span>
                    )}
                  </div>
                  
                  <div className="mt-2 text-sm text-gray-500">
                    <p>Скрипт: {process.script_path}</p>
                    {process.pid && <p>PID: {process.pid}</p>}
                    {process.start_time && <p>Запущен: {new Date(process.start_time).toLocaleString()}</p>}
                    {process.restart_count > 0 && <p>Перезапусков: {process.restart_count}</p>}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {process.status === 'running' && (
                    <button
                      onClick={() => onAction(process.id, 'stop')}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Остановить
                    </button>
                  )}
                  
                  {process.status === 'stopped' && (
                    <button
                      onClick={() => onAction(process.id, 'restart')}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      Перезапустить
                    </button>
                  )}
                  
                  <button
                    onClick={() => handleShowLogs(process.id)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    {selectedProcess === process.id ? 'Скрыть логи' : 'Показать логи'}
                  </button>
                  
                  <button
                    onClick={() => onDelete(process.id)}
                    className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    Удалить
                  </button>
                </div>
              </div>
              
              {/* Логи процесса */}
              {selectedProcess === process.id && (
                <div className="mt-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Логи процесса</h4>
                    {loadingLogs ? (
                      <div className="flex justify-center py-4">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      </div>
                    ) : (
                      <div className="bg-black text-green-400 p-3 rounded text-sm font-mono max-h-64 overflow-y-auto">
                        {logs.length === 0 ? (
                          <p className="text-gray-500">Логи отсутствуют</p>
                        ) : (
                          logs.map((log, index) => (
                            <div key={index} className="whitespace-pre-wrap">{log}</div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}; 