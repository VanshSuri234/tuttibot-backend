import React, { useState, useEffect, useRef } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "./components/ui/card";
import { BarChart3, FileAudio, FileText, Play, CheckCircle, AlertCircle, Loader2, MessageSquare, Music, Bot, BookOpen, Send } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [audioFile, setAudioFile] = useState(null);
  const [scoreFile, setScoreFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [status, setStatus] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  // --- NEW STATES FOR CHAT FUNCTIONALITY ---
  const [jobId, setJobId] = useState(null);
  const [inputText, setInputText] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', content: "Hello! I'm TuttiBot. Upload your audio recording and musical score, and I'll analyze your performance!" }
  ]);
  const chatContainerRef = useRef(null);

  // Auto-scroll to the bottom of the chat when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isChatting]);

  const handleFileChange = (e, type) => {
    const file = e.target.files[0];
    if (type === 'audio') setAudioFile(file);
    else setScoreFile(file);
  };

  const startAnalysis = async () => {
    if (!audioFile || !scoreFile) return;

    setIsAnalyzing(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('score_file', scoreFile);

    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      if (response.ok) {
        setStatus('queued');
        setJobId(data.job_id); // Store ID for the Chat endpoint
        pollStatus(data.job_id);
      } else {
        setError(data.error || 'Analysis failed to start');
        setIsAnalyzing(false);
      }
    } catch (err) {
      setError('Network error');
      setIsAnalyzing(false);
    }
  };

  const pollStatus = async (id) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/status/${id}`);
        const data = await response.json();
        
        setStatus(data.status);
        
        if (data.status === 'completed') {
          clearInterval(interval);
          fetchResults(id);
        } else if (data.status === 'failed') {
          clearInterval(interval);
          setIsAnalyzing(false);
          setError(data.error || 'Analysis failed');
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 2000);
  };

  const fetchResults = async (id) => {
    try {
      const response = await fetch(`/results/${id}`);
      const data = await response.json();
      if (response.ok) {
        setAnalysisResult(data.results);
        setIsAnalyzing(false);
        setActiveTab("performance"); 
        
        // Add a bot notification to the chat
        setMessages(prev => [...prev, { 
          role: 'bot', 
          content: `Analysis complete! Your overall score is ${data.results?.grade_data?.overall_score || 'available now'}. What would you like to know about it?` 
        }]);
      }
    } catch (err) {
      console.error("Fetch results error", err);
      setIsAnalyzing(false);
    }
  };

  // --- NEW HANDLER FOR CHAT ---
  const handleSendMessage = async (e) => {
    e?.preventDefault();
    if (!inputText.trim() || isChatting) return;

    const userMessage = inputText;
    setInputText("");
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    if (!jobId) {
      setMessages(prev => [...prev, { role: 'bot', content: "Please analyze a performance first so I have data to discuss with you!" }]);
      return;
    }

    setIsChatting(true);
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          message: userMessage,
          history: messages.slice(-10) // Send recent history for context
        }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'bot', content: data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', content: "I'm having trouble connecting to the chat service right now." }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Music className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600" style={{ fontFamily: 'Playfair Display, serif' }}>
              TuttiBot
            </h1>
          </div>
          <nav>
            <ul className="flex gap-6 text-sm font-medium text-slate-600">
              <li className="hover:text-blue-600 cursor-pointer transition-colors">Documentation</li>
              <li className="hover:text-blue-600 cursor-pointer transition-colors">About</li>
              <li className="hover:text-blue-600 cursor-pointer transition-colors">Settings</li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          <TabsList className="grid w-full grid-cols-4 max-w-2xl mx-auto bg-white border border-slate-200 shadow-sm rounded-xl p-1">
            <TabsTrigger value="chat" className="data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700">
              <MessageSquare className="h-4 w-4 mr-2" /> Chat
            </TabsTrigger>
            <TabsTrigger value="performance" className="data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700">
              <BarChart3 className="h-4 w-4 mr-2" /> Analysis
            </TabsTrigger>
            <TabsTrigger value="research" className="data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700">
              <BookOpen className="h-4 w-4 mr-2" /> Research
            </TabsTrigger>
            <TabsTrigger value="hri" className="data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700">
              <Bot className="h-4 w-4 mr-2" /> HRI Design
            </TabsTrigger>
          </TabsList>

          {/* Chat / Upload Tab */}
          <TabsContent value="chat" className="max-w-4xl mx-auto">
            <div className="grid md:grid-cols-3 gap-6">
              <div className="md:col-span-2 space-y-4">
                <Card className="bg-white border-2 border-blue-100 shadow-lg h-[600px] flex flex-col">
                  <CardHeader className="border-b border-slate-100">
                    <CardTitle className="flex items-center gap-2 text-blue-700">
                      <Bot className="h-5 w-5" /> TuttiBot Assistant
                    </CardTitle>
                    <CardDescription>Chat with TuttiBot about your performance or upload files for analysis</CardDescription>
                  </CardHeader>
                  
                  {/* DYNAMIC CHAT CONTENT */}
                  <CardContent ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.map((msg, index) => (
                      <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-indigo-100' : 'bg-blue-100'}`}>
                          {msg.role === 'user' ? (
                            <div className="h-5 w-5 text-indigo-600 font-bold text-xs flex items-center justify-center">You</div>
                          ) : (
                            <Bot className="h-5 w-5 text-blue-600" />
                          )}
                        </div>
                        <div className={`p-3 rounded-2xl max-w-[80%] text-sm ${
                          msg.role === 'user' 
                          ? 'bg-blue-600 text-white rounded-tr-none' 
                          : 'bg-slate-100 text-slate-700 rounded-tl-none'
                        }`}>
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {isChatting && (
                      <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                        </div>
                        <div className="bg-slate-100 p-3 rounded-2xl rounded-tl-none text-slate-400 text-sm italic">
                          TuttiBot is thinking...
                        </div>
                      </div>
                    )}
                  </CardContent>

                  <div className="p-4 border-t border-slate-100">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                      <input 
                        type="text" 
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        placeholder="Type a message..." 
                        className="flex-1 px-4 py-2 rounded-full border border-slate-200 focus:outline-none focus:border-blue-400 text-sm" 
                      />
                      <button 
                        type="submit"
                        disabled={!inputText.trim() || isChatting}
                        className="bg-blue-600 text-white p-2 rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50"
                      >
                        <Send className="h-4 w-4 ml-0.5" />
                      </button>
                    </form>
                  </div>
                </Card>
              </div>

              <div className="space-y-4">
                <Card className="bg-white border-2 border-indigo-50 shadow-md">
                  <CardHeader>
                    <CardTitle className="text-indigo-700 text-lg">Upload Files</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">Audio Recording</label>
                      <div className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${audioFile ? 'border-green-400 bg-green-50' : 'border-slate-200 hover:border-blue-400'}`}>
                        <input type="file" accept="audio/*" onChange={(e) => handleFileChange(e, 'audio')} className="hidden" id="audio-upload" />
                        <label htmlFor="audio-upload" className="cursor-pointer block">
                          {audioFile ? (
                            <div className="flex items-center justify-center gap-2 text-green-700">
                              <CheckCircle className="h-5 w-5" />
                              <span className="text-sm truncate max-w-[150px]">{audioFile.name}</span>
                            </div>
                          ) : (
                            <div className="flex flex-col items-center gap-2 text-slate-400">
                              <FileAudio className="h-8 w-8" />
                              <span className="text-xs">Click to upload audio</span>
                            </div>
                          )}
                        </label>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-slate-700">Musical Score</label>
                      <div className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${scoreFile ? 'border-green-400 bg-green-50' : 'border-slate-200 hover:border-blue-400'}`}>
                        <input type="file" accept=".pdf,.xml,.musicxml,.mid" onChange={(e) => handleFileChange(e, 'score')} className="hidden" id="score-upload" />
                        <label htmlFor="score-upload" className="cursor-pointer block">
                          {scoreFile ? (
                            <div className="flex items-center justify-center gap-2 text-green-700">
                              <CheckCircle className="h-5 w-5" />
                              <span className="text-sm truncate max-w-[150px]">{scoreFile.name}</span>
                            </div>
                          ) : (
                            <div className="flex flex-col items-center gap-2 text-slate-400">
                              <FileText className="h-8 w-8" />
                              <span className="text-xs">Click to upload score</span>
                            </div>
                          )}
                        </label>
                      </div>
                    </div>

                    <button 
                      onClick={startAnalysis}
                      disabled={!audioFile || !scoreFile || isAnalyzing}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2.5 rounded-lg font-medium hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" /> Processing...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4" /> Run Analysis
                        </>
                      )}
                    </button>

                    {error && (
                      <div className="bg-red-50 text-red-600 p-3 rounded-lg text-xs flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                        {error}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Performance Analysis Tab */}
          <TabsContent value="performance" className="max-w-5xl mx-auto">
            {analysisResult && analysisResult.grade_data ? (
              <div className="space-y-6">
                <Card className="bg-white border-2 border-blue-200 shadow-xl">
                  <CardHeader className="border-b border-blue-100 bg-gradient-to-r from-blue-50 to-white">
                    <CardTitle className="text-blue-600 flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                      🎯 Performance Analysis Results
                    </CardTitle>
                    <CardDescription className="text-slate-600">Detailed feedback and metrics</CardDescription>
                  </CardHeader>
                  <CardContent className="p-6 space-y-6">
                    
                    {/* Overall Score Display */}
                    {analysisResult.grade_data.overall_score !== undefined && (
                      <div className="bg-gradient-to-r from-blue-100 to-purple-100 rounded-lg p-8 text-center border-2 border-blue-300">
                        <p className="text-slate-600 font-semibold text-sm uppercase tracking-wide">Your Performance Score</p>
                        <div className="text-6xl font-bold text-blue-600 my-4">{analysisResult.grade_data.overall_score.toFixed(1)}</div>
                        <p className="text-slate-600">out of 100</p>
                        <div className="mt-4 w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                          <div 
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-full rounded-full transition-all" 
                            style={{ width: `${Math.min(analysisResult.grade_data.overall_score, 100)}%` }}
                          />
                        </div>
                      </div>
                    )}
                    
                    {/* Component Scores Chart */}
                    {analysisResult.grade_data.components && (
                      <Card className="bg-white border-2 border-blue-200">
                        <CardHeader className="bg-gradient-to-r from-blue-50 to-white">
                          <CardTitle className="text-blue-600 text-lg flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                            📊 Component Scores
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="h-80">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                              data={Object.entries(analysisResult.grade_data.components).map(([name, score]) => ({ name, score }))}
                              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis domain={[0, 100]} />
                              <Tooltip />
                              <Legend />
                              <Bar dataKey="score" fill="#2563eb" name="Score (%)" />
                            </BarChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    )}

                    {/* Detailed Metrics */}
                    {analysisResult.grade_data.detailed_metrics && (
                      <div className="grid md:grid-cols-2 gap-6">
                        {Object.entries(analysisResult.grade_data.detailed_metrics).map(([category, metrics]) => (
                          <Card key={category} className="bg-white border-2 border-blue-200">
                            <CardHeader className="bg-gradient-to-r from-blue-50 to-white">
                              <CardTitle className="text-blue-600 text-lg flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                                📝 {category}
                              </CardTitle>
                            </CardHeader>
                            <CardContent>
                              <ul className="space-y-3">
                                {Object.entries(metrics).map(([key, value]) => (
                                  <li key={key} className="flex justify-between items-center border-b border-slate-100 pb-2 last:border-0">
                                    <span className="text-slate-600 font-medium">{key}</span>
                                    <span className="text-blue-700 font-bold">{value}</span>
                                  </li>
                                ))}
                              </ul>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    )}

                    {/* Full Report */}
                    {analysisResult.report_text && (
                       <Card className="bg-gradient-to-br from-blue-50 to-white border-2 border-blue-200 mt-6">
                        <CardHeader>
                          <CardTitle className="text-blue-600 text-lg flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                            📄 Full Report
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <pre className="whitespace-pre-wrap text-slate-700 text-sm font-mono overflow-auto max-h-96">
                            {analysisResult.report_text}
                          </pre>
                        </CardContent>
                      </Card>
                    )}

                    <p className="text-blue-600 mt-6 font-medium bg-blue-50 p-4 rounded-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      💡 Use the Chat tab to discuss your HRI design ideas with TuttiBot!
                    </p>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="bg-white border-2 border-blue-200 shadow-xl">
                <CardContent className="py-12 text-center">
                  <BarChart3 className="h-16 w-16 mx-auto text-blue-400 mb-4" />
                  <p className="text-blue-600 text-lg font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>📊 No analysis available yet</p>
                  <p className="text-slate-600 text-sm mt-2" style={{ fontFamily: 'Manrope, sans-serif' }}>Upload files in the Chat tab and run analysis to see results here</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Research Tab - FULL CONTENT PRESERVED */}
          <TabsContent value="research" className="max-w-5xl mx-auto">
            <Card className="bg-white border-2 border-blue-200 shadow-xl">
              <CardHeader className="border-b border-blue-100 bg-gradient-to-r from-blue-50 to-white">
                <CardTitle className="text-blue-600 flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                  🔬 Research Explorer
                </CardTitle>
                <CardDescription className="text-slate-600">Explore cutting-edge research in music AI and robotics</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 pt-6">
                <div className="max-w-none">
                  <h3 className="text-2xl font-bold text-blue-600 mb-4 flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                    📚 Research Topics
                  </h3>
                  <div className="grid md:grid-cols-2 gap-4 mt-4">
                    <div className="bg-gradient-to-br from-blue-50 to-white p-5 rounded-xl border-2 border-blue-200 hover:border-blue-400 hover:shadow-lg transition-all">
                      <h4 className="text-blue-600 mb-2 font-bold flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                        🎯 Performance Grading
                      </h4>
                      <p className="text-sm text-slate-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        AI-based systems for evaluating pitch accuracy, timing precision, and musical expression using signal processing and machine learning.
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-cyan-50 to-white p-5 rounded-xl border-2 border-cyan-200 hover:border-cyan-400 hover:shadow-lg transition-all">
                      <h4 className="text-cyan-600 mb-2 font-bold flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                        🤖 Robot Orchestras
                      </h4>
                      <p className="text-sm text-slate-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        Coordination algorithms and synchronization methods for human-robot ensemble performance and adaptive conducting.
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-violet-50 to-white p-5 rounded-xl border-2 border-violet-200 hover:border-violet-400 hover:shadow-lg transition-all">
                      <h4 className="text-violet-600 mb-2 font-bold flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                        🎵 Audio Analysis
                      </h4>
                      <p className="text-sm text-slate-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        Advanced techniques like pYIN for pitch detection, MIDI alignment, and spectral analysis for music information retrieval.
                      </p>
                    </div>
                    <div className="bg-gradient-to-br from-emerald-50 to-white p-5 rounded-xl border-2 border-emerald-200 hover:border-emerald-400 hover:shadow-lg transition-all">
                      <h4 className="text-emerald-600 mb-2 font-bold flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                        🎼 Expressive AI
                      </h4>
                      <p className="text-sm text-slate-700" style={{ fontFamily: 'Manrope, sans-serif' }}>
                        Machine learning models for understanding and generating musical expression, dynamics, and interpretive choices.
                      </p>
                    </div>
                  </div>
                  <p className="text-blue-600 mt-6 font-medium bg-blue-50 p-4 rounded-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    💡 Chat with TuttiBot to dive deeper into any research area or get guidance on your own research!
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* HRI Tab - FULL CONTENT PRESERVED */}
          <TabsContent value="hri" className="max-w-5xl mx-auto">
            <Card className="bg-white border-2 border-blue-200 shadow-xl">
              <CardHeader className="border-b border-blue-100 bg-gradient-to-r from-blue-50 to-white">
                <CardTitle className="text-blue-600 flex items-center gap-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                  🤖 Human-Robot Interaction Design
                </CardTitle>
                <CardDescription className="text-slate-600">Design and explore robot-human orchestra interactions</CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <p className="text-slate-700 mb-4">
                  This section allows you to configure how the robot interacts with human performers.
                </p>
                <div className="grid md:grid-cols-3 gap-4">
                  <Card className="bg-slate-50 border border-slate-200">
                    <CardHeader>
                      <CardTitle className="text-base">Visual Cues</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600">Configure LED patterns and gestures for conducting.</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-slate-50 border border-slate-200">
                    <CardHeader>
                      <CardTitle className="text-base">Adaptive Timing</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600">Adjust how quickly the robot adapts to tempo changes.</p>
                    </CardContent>
                  </Card>
                  <Card className="bg-slate-50 border border-slate-200">
                    <CardHeader>
                      <CardTitle className="text-base">Feedback Mode</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600">Select between real-time, post-performance, or educational modes.</p>
                    </CardContent>
                  </Card>
                </div>
                <p className="text-blue-600 mt-6 font-medium bg-blue-50 p-4 rounded-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  💡 Use the Chat tab to discuss your HRI design ideas with TuttiBot!
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;