import apiClient from './api';

export const aiService = {
  async chatWithAssistant({ message, conversationHistory = [], sessionId = null, destinationHint = null }) {
    const payload = {
      message,
      conversation_history: conversationHistory.map((m) => ({
        role: m.role,
        content: m.content,
      })),
      session_id: sessionId,
      destination_hint: destinationHint,
    };
    const response = await apiClient.post('/ai/chat', payload);
    return response.data;
  },

  async extractPreferences(text) {
    const response = await apiClient.post('/ai/extract-preferences', { text });
    return response.data;
  },
};

export default aiService;

