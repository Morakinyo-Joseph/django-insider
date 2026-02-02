import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import { GripVertical, ChevronDown, ChevronUp, CheckCircle2, HelpCircle } from "lucide-react"; // Removed Puzzle
import ConfigForm from "../../components/integrations/ConfigForm";
import { fetchIntegrations, toggleIntegration, reorderIntegrations, saveIntegrationConfig } from "../../api/client";

export default function Integrations() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<string | null>(null);
  
  // New state for toggling the help text
  const [showInfo, setShowInfo] = useState(false);

  const [localIntegrations, setLocalIntegrations] = useState<any[]>([]);

  // 1. Fetch Data
  const { data: integrations, isLoading } = useQuery({
    queryKey: ["integrations"],
    queryFn: fetchIntegrations,
  });

  useEffect(() => {
    if (integrations) {
      setLocalIntegrations(integrations);
    }
  }, [integrations]);

  // 2. Mutations (Unchanged)
  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) => 
      toggleIntegration(id, isActive),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["integrations"] }),
  });

  const reorderMutation = useMutation({
    mutationFn: reorderIntegrations,
    onSuccess: () => { /* Silent success */ }
  });

  const saveConfigMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => saveIntegrationConfig(id, data),
    onSuccess: () => {
      setEditingId(null);
      queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });

  // 3. Handlers
  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const items = Array.from(localIntegrations);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);

    setLocalIntegrations(items);
    const newOrderIds = items.map(i => i.identifier);
    reorderMutation.mutate({ order: newOrderIds });
  };

  const handleToggle = (id: string, currentStatus: boolean) => {
    setLocalIntegrations(prev => 
        prev.map(i => i.identifier === id ? { ...i, is_active: !currentStatus } : i)
    );
    toggleMutation.mutate({ id, isActive: !currentStatus });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-20">
      
      {/* --- CLEAN HEADER SECTION --- */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <h1 className="text-2xl font-bold text-gray-900">Integrations Pipeline</h1>
          <button 
            onClick={() => setShowInfo(!showInfo)}
            className={`p-1 rounded-full transition-colors ${showInfo ? 'text-indigo-600 bg-indigo-50' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'}`}
            title="How does this work?"
          >
            <HelpCircle size={18} />
          </button>
        </div>

        {/* Collapsible Info Box */}
        {showInfo && (
          <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 text-sm text-indigo-900 animate-in fade-in slide-in-from-top-1">
            <p>
              <strong>Pipeline Logic:</strong> Insider processes errors in the order shown below. 
              Data flows from the top card <strong>(01)</strong> downwards. 
            </p>
            <p className="mt-1 text-indigo-700">
              Drag and drop cards to change the execution order. Use the toggle to enable/disable specific steps.
            </p>
          </div>
        )}
      </div>


      {/* --- LIST SECTION (Unchanged) --- */}
      {isLoading ? (
        <div className="space-y-4">
            {[1, 2, 3].map(i => (
                <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
            ))}
        </div>
      ) : (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="integrations-list">
            {(provided) => (
              <div 
                {...provided.droppableProps} 
                ref={provided.innerRef}
                className="space-y-4"
              >
                {localIntegrations.map((integration, index) => (
                  <Draggable 
                    key={integration.identifier} 
                    draggableId={integration.identifier} 
                    index={index}
                  >
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        className={`group bg-white border rounded-xl transition-all duration-200 ${
                          snapshot.isDragging 
                            ? "shadow-xl ring-2 ring-indigo-500 rotate-1 border-transparent z-50" 
                            : "shadow-sm border-gray-200 hover:border-indigo-200"
                        }`}
                      >
                        <div className="flex items-center p-4">
                          {/* Drag Handle */}
                          <div 
                            {...provided.dragHandleProps}
                            className="mr-4 text-gray-300 hover:text-gray-600 cursor-grab active:cursor-grabbing p-1 rounded hover:bg-gray-50"
                          >
                            <GripVertical size={20} />
                          </div>

                          {/* Order Number */}
                          <div className="mr-6 font-mono text-xl font-bold text-gray-200 select-none">
                            {String(index + 1).padStart(2, '0')}
                          </div>

                          {/* LOGO (New!) */}
                          {/* We use a fixed width container to ensure alignment even if logo is missing */}
                          <div className="mr-4 w-8 h-8 flex-shrink-0 flex items-center justify-center bg-gray-50 rounded-lg p-1 border border-gray-100">
                             {integration.logo_url ? (
                                <img 
                                    src={integration.logo_url} 
                                    alt={integration.name} 
                                    className="w-full h-full object-contain"
                                />
                             ) : (
                                // Fallback if no URL: First letter of name
                                <span className="text-xs font-bold text-gray-400">
                                    {integration.name.charAt(0)}
                                </span>
                             )}
                          </div>

                          {/* Name & Status */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3">
                              <h3 className="text-base font-semibold text-gray-900">
                                {integration.name}
                              </h3>
                              
                              {/* --- RESTORED STATUS BADGES --- */}
                              {integration.is_active ? (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-50 text-green-700 border border-green-200">
                                  <CheckCircle2 size={10} className="text-green-600" />
                                  Active
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-500 border border-gray-200">
                                  Disabled
                                </span>
                              )}    
                            </div>
                            <p className="text-xs text-gray-400 mt-0.5 truncate">
                              {index === 0 
                                ? "Starts the pipeline (Producer)" 
                                : "Runs after previous step"
                              }
                            </p>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-4">
                            <button
                                onClick={() => handleToggle(integration.identifier, integration.is_active)}
                                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
                                    integration.is_active ? "bg-indigo-600" : "bg-gray-200"
                                }`}
                            >
                                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                    integration.is_active ? "translate-x-6" : "translate-x-1"
                                }`} />
                            </button>

                            <div className="h-8 w-px bg-gray-100 mx-1"></div>

                            <button
                                onClick={() => setEditingId(
                                    editingId === integration.identifier ? null : integration.identifier
                                )}
                                className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors border ${
                                    editingId === integration.identifier
                                        ? "bg-indigo-50 text-indigo-700 border-indigo-200"
                                        : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
                                }`}
                            >
                                Configure
                                {editingId === integration.identifier ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            </button>
                          </div>
                        </div>

                        {/* CONFIG DRAWER */}
                        {editingId === integration.identifier && (
                          <ConfigForm 
                            integration={integration}
                            onSave={(id, data) => saveConfigMutation.mutate({ id, data })}
                            onCancel={() => setEditingId(null)}
                            isSaving={saveConfigMutation.isPending}
                          />
                        )}
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      )}
    </div>
  );
}