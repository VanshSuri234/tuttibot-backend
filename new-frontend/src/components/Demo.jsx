import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart3, FileAudio, FileText, Play, CheckCircle, 
  AlertCircle, Loader2, MessageSquare, Music, Bot, 
  BookOpen, Send, UserCircle, Cpu, Layers 
} from "lucide-react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

// UI Components
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";

// Asset Import - Ensure path matches your file structure
import demoVideo from "../assets/GEM_AI_DEMO.mp4";

const Demo = () => {
  // --- STATES ---
  const [activeTab, setActiveTab] = useState("chat");
  const [audioFile, setAudioFile] = useState(null);
  const [scoreFile, setScoreFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [status, setStatus] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [inputText, setInputText] = useState("");
  const [isChatting, setIsChatting] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', content: "Hello! I'm TuttiBot. Upload your audio recording and musical score below, and I'll analyze your performance!" }
  ]);
  const chatContainerRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isChatting]);

  // --- HANDLERS ---
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
      const response = await fetch('https://tuttibot-backend.onrender.com/upload', { method: 'POST', body: formData });
      const data = await response.json();
      if (response.ok) {
        setStatus('queued');
        setJobId(data.job_id);
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
        const response = await fetch(`https://tuttibot-backend.onrender.com/status/${id}`);
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
      } catch (err) { console.error("Polling error", err); }
    }, 2000);
  };

  const fetchResults = async (id) => {
    try {
      const response = await fetch(`https://tuttibot-backend.onrender.com/results/${id}`);
      const data = await response.json();
      if (response.ok) {
        setAnalysisResult(data.results);
        setIsAnalyzing(false);
        setActiveTab("performance");
        setMessages(prev => [...prev, { 
          role: 'bot', 
          content: `Analysis complete! Your overall score is ${data.results?.grade_data?.overall_score || 'available now'}. What would you like to know about it?` 
        }]);
      }
    } catch (err) { setIsAnalyzing(false); }
  };

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
      const response = await fetch('https://tuttibot-backend.onrender.com/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ job_id: jobId, message: userMessage, history: messages.slice(-10) }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'bot', content: data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', content: "I'm having trouble connecting to the chat service." }]);
    } finally { setIsChatting(false); }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* 1. HEADER */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg"><Music className="h-6 w-6 text-white" /></div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
              TuttiBot Demo
            </h1>
          </div>
          <nav className="hidden md:block">
            <ul className="flex gap-6 text-sm font-medium text-slate-600">
              <li className="hover:text-blue-600 cursor-pointer transition-colors">Documentation</li>
              <li className="hover:text-blue-600 cursor-pointer transition-colors">About</li>
              <li className="hover:text-blue-600 cursor-pointer transition-colors">Settings</li>
            </ul>
          </nav>
        </div>
      </header>

      {/* 2. VIDEO SECTION */}
      <section className="bg-slate-900 py-12">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-white mb-2">Watch How GEM AI Works</h2>
              <p className="text-slate-400">See TuttiBot analyze a live performance in real-time</p>
            </div>
            <div className="relative rounded-2xl overflow-hidden shadow-2xl border-4 border-slate-800 bg-black aspect-video">
              <video src={demoVideo} controls className="w-full h-full object-cover">
                Your browser does not support video playback.
              </video>
            </div>
          </div>
        </div>
      </section>

      {/* 3. MAIN INTERACTIVE SECTION */}
      <main className="container mx-auto px-4 py-12">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          <div className="flex justify-center">
            <TabsList className="bg-white border shadow-sm rounded-xl p-1 h-auto">
              <TabsTrigger value="chat" className="px-6 py-2 data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700">
                <MessageSquare className="h-4 w-4 mr-2" /> Chat
              </TabsTrigger>
              <TabsTrigger value="performance" className="px-6 py-2">
                <BarChart3 className="h-4 w-4 mr-2" /> Analysis
              </TabsTrigger>
              <TabsTrigger value="research" className="px-6 py-2">
                <BookOpen className="h-4 w-4 mr-2" /> Research
              </TabsTrigger>
              <TabsTrigger value="hri" className="px-6 py-2">
                <Bot className="h-4 w-4 mr-2" /> HRI Design
              </TabsTrigger>
            </TabsList>
          </div>

          {/* CHAT TAB */}
          <TabsContent value="chat" className="max-w-6xl mx-auto outline-none">
            <div className="grid md:grid-cols-3 gap-6">
              <div className="md:col-span-2">
                <Card className="bg-white border-2 border-blue-100 shadow-lg h-[600px] flex flex-col rounded-2xl overflow-hidden">
                  <CardHeader className="border-b bg-slate-50/50">
                    <CardTitle className="flex items-center gap-2 text-blue-700">
                      <Bot className="h-5 w-5" /> TuttiBot Assistant
                    </CardTitle>
                  </CardHeader>
                  <CardContent ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4 bg-white">
                    {messages.map((msg, index) => (
                      <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-indigo-100 text-indigo-600 font-bold text-xs' : 'bg-blue-100'}`}>
                          {msg.role === 'user' ? "YOU" : <Bot className="h-5 w-5 text-blue-600" />}
                        </div>
                        <div className={`p-3 rounded-2xl max-w-[80%] text-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-slate-100 text-slate-700 rounded-tl-none'}`}>
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {isChatting && (
                      <div className="flex gap-3 animate-pulse">
                        <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center"><Loader2 className="h-4 w-4 animate-spin text-blue-600" /></div>
                        <div className="bg-slate-100 p-3 rounded-2xl rounded-tl-none text-slate-400 text-sm italic">TuttiBot is thinking...</div>
                      </div>
                    )}
                  </CardContent>
                  <div className="p-4 border-t bg-slate-50">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                      <input 
                        value={inputText} 
                        onChange={(e) => setInputText(e.target.value)}
                        placeholder="Type a message..." 
                        className="flex-1 px-4 py-2 rounded-full border border-slate-200 focus:ring-2 focus:ring-blue-500 outline-none text-sm" 
                      />
                      <button type="submit" className="bg-blue-600 text-white p-2 rounded-full hover:bg-blue-700 disabled:opacity-50">
                        <Send className="h-5 w-5" />
                      </button>
                    </form>
                  </div>
                </Card>
              </div>

              {/* UPLOAD PANEL */}
              <div className="space-y-4">
                <Card className="border-2 border-indigo-50 shadow-md">
                  <CardHeader><CardTitle className="text-indigo-700 text-lg">Upload Performance</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">Audio Recording</label>
                      <div onClick={() => document.getElementById('audio-up').click()} className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${audioFile ? 'border-green-400 bg-green-50' : 'border-slate-200 hover:border-blue-400'}`}>
                        <input type="file" id="audio-up" hidden onChange={(e) => handleFileChange(e, 'audio')} />
                        {audioFile ? <div className="flex items-center justify-center gap-2 text-green-700 text-sm font-medium"><CheckCircle className="h-4 w-4" /> {audioFile.name}</div> : <div className="text-slate-400 text-xs"><FileAudio className="h-6 w-6 mx-auto mb-1" /> Click to upload</div>}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold text-slate-500 uppercase">Musical Score</label>
                      <div onClick={() => document.getElementById('score-up').click()} className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${scoreFile ? 'border-green-400 bg-green-50' : 'border-slate-200 hover:border-blue-400'}`}>
                        <input type="file" id="score-up" hidden onChange={(e) => handleFileChange(e, 'score')} />
                        {scoreFile ? <div className="flex items-center justify-center gap-2 text-green-700 text-sm font-medium"><CheckCircle className="h-4 w-4" /> {scoreFile.name}</div> : <div className="text-slate-400 text-xs"><FileText className="h-6 w-6 mx-auto mb-1" /> Click to upload</div>}
                      </div>
                    </div>
                    <button 
                      onClick={startAnalysis} 
                      disabled={!audioFile || !scoreFile || isAnalyzing}
                      className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                    >
                      {isAnalyzing ? <><Loader2 className="h-4 w-4 animate-spin" /> Processing...</> : <><Play className="h-4 w-4" /> Run Analysis</>}
                    </button>
                    {error && <div className="text-red-500 text-xs flex gap-1 mt-2"><AlertCircle className="h-4 w-4" /> {error}</div>}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* PERFORMANCE TAB */}
          <TabsContent value="performance" className="max-w-5xl mx-auto">
            {analysisResult ? (
              <div className="space-y-6">
                <Card className="border-2 border-blue-200 shadow-xl overflow-hidden">
                  <div className="bg-blue-600 p-4 text-white font-bold">🎯 Performance Metrics</div>
                  <CardContent className="p-6">
                    <div className="h-80 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={Object.entries(analysisResult.grade_data.components).map(([name, score]) => ({ name, score }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis domain={[0, 100]} />
                          <Tooltip />
                          <Bar dataKey="score" fill="#2563eb" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="text-center py-20 border-2 border-dashed rounded-3xl text-slate-400">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-20" />
                <p>Run an analysis in the Chat tab to see charts here.</p>
              </div>
            )}
          </TabsContent>

          {/* RESEARCH TAB - ENHANCED CONTENT */}
          <TabsContent value="research" className="max-w-5xl mx-auto">
            <div className="grid gap-6">
              <Card className="bg-white border-2 border-blue-200 shadow-xl overflow-hidden">
                <CardHeader className="border-b border-blue-100 bg-gradient-to-r from-blue-50 to-white">
                  <CardTitle className="text-blue-600 flex items-center gap-2">
                    <BookOpen className="h-6 w-6" /> Research Explorer
                  </CardTitle>
                  <CardDescription className="text-slate-600">Investigating the intersection of Machine Listening and Robotic Artistry</CardDescription>
                </CardHeader>
                <CardContent className="p-8 space-y-10">
                  <div>
                    <h3 className="text-xl font-bold text-slate-800 mb-6 border-l-4 border-blue-600 pl-3">Fundamental Research Pillars</h3>
                    <div className="grid md:grid-cols-3 gap-6">
                      <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-100">
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600"><Music className="h-5 w-5" /></div>
                        <h4 className="font-bold text-slate-800">Machine Listening</h4>
                        <p className="text-xs text-slate-600 leading-relaxed">Implementing <strong>pYIN algorithms</strong> for robust fundamental frequency estimation in polyphonic environments.</p>
                      </div>
                      <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-100">
                        <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600"><BarChart3 className="h-5 w-5" /></div>
                        <h4 className="font-bold text-slate-800">Performance Alignment</h4>
                        <p className="text-xs text-slate-600 leading-relaxed">Utilizing <strong>Dynamic Time Warping (DTW)</strong> to map live audio streams to musical scores in real-time.</p>
                      </div>
                      <div className="space-y-3 p-4 rounded-xl bg-slate-50 border border-slate-100">
                        <div className="w-10 h-10 rounded-full bg-violet-100 flex items-center justify-center text-violet-600"><Bot className="h-5 w-5" /></div>
                        <h4 className="font-bold text-slate-800">Social Robotics</h4>
                        <p className="text-xs text-slate-600 leading-relaxed">Studying the <strong>Uncanny Valley</strong> and how anthropomorphic cues affect ensemble cohesion.</p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200">
                    <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2"><FileText className="h-5 w-5 text-blue-600" /> Reference Knowledge Base</h3>
                    <div className="space-y-3">
                      {[
                        { tag: "Journal", title: "Real-time Tempo Tracking for Human-Robot Duets", author: "Dr. A. Sterling, 2025" },
                        { tag: "Paper", title: "Cross-Modal Emotional Mapping in Musical HRI", author: "TuttiBot Labs, 2024" },
                        { tag: "Technical", title: "Optimizing MIDI-to-Audio Latency in Linux", author: "Internal Report v2.1" }
                      ].map((item, i) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-100 shadow-sm group hover:border-blue-400 transition-colors">
                          <div className="flex items-center gap-4">
                            <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-600 px-2 py-1 rounded">{item.tag}</span>
                            <p className="text-sm font-medium text-slate-700">{item.title}</p>
                          </div>
                          <span className="text-xs text-slate-400 italic">{item.author}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
          
          {/* HRI TAB - ENHANCED CONTENT */}
          <TabsContent value="hri" className="max-w-5xl mx-auto">
            <Card className="bg-white border-2 border-blue-200 shadow-xl overflow-hidden">
              <CardHeader className="border-b border-blue-100 bg-gradient-to-r from-blue-50 to-white">
                <CardTitle className="text-blue-600 flex items-center gap-2">🤖 HRI Interaction Framework</CardTitle>
                <CardDescription>Defining the feedback loops between human performers and TuttiBot</CardDescription>
              </CardHeader>
              <CardContent className="p-8">
                <div className="grid md:grid-cols-2 gap-12">
                  <div className="space-y-8">
                    <section>
                      <h3 className="text-sm font-bold text-blue-600 uppercase tracking-widest mb-4">Interaction Modalities</h3>
                      <div className="space-y-4">
                        <div className="flex gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                          <div className="bg-white p-2 h-fit rounded-lg shadow-sm"><Music className="h-5 w-5 text-blue-500" /></div>
                          <div>
                            <h4 className="text-sm font-bold text-slate-800">Auditory Feedback</h4>
                            <p className="text-xs text-slate-600 mt-1">Real-time tempo adjustment through robotic accompaniment volume and timing density.</p>
                          </div>
                        </div>
                        <div className="flex gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                          <div className="bg-white p-2 h-fit rounded-lg shadow-sm"><AlertCircle className="h-5 w-5 text-amber-500" /></div>
                          <div>
                            <h4 className="text-sm font-bold text-slate-800">Visual Cues (LED Matrix)</h4>
                            <p className="text-xs text-slate-600 mt-1">Utilizing color-coded pulses (Red: Sharp, Blue: Flat) for non-intrusive intonation feedback.</p>
                          </div>
                        </div>
                        <div className="flex gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                          <div className="bg-white p-2 h-fit rounded-lg shadow-sm"><Bot className="h-5 w-5 text-indigo-500" /></div>
                          <div>
                            <h4 className="text-sm font-bold text-slate-800">Gestural Conducting</h4>
                            <p className="text-xs text-slate-600 mt-1">Mapping robot arm velocity to orchestral dynamics for expressive leadership.</p>
                          </div>
                        </div>
                      </div>
                    </section>
                  </div>
                  <div className="relative">
                    <div className="bg-slate-900 rounded-3xl p-8 h-full flex flex-col justify-between text-center border-4 border-slate-800 shadow-2xl">
                      <h3 className="text-blue-400 font-mono text-xs uppercase tracking-tighter mb-4">Internal System Loop</h3>
                      <div className="space-y-6">
                        <div className="p-3 border border-blue-500/30 rounded bg-blue-500/10 text-blue-300 font-mono text-[10px]">PERCEPTION: Mic Input -{'>'} FFT -{'>'} Pitch Detection</div>
                        <div className="flex justify-center"><Loader2 className="h-4 w-4 text-slate-600 animate-spin" /></div>
                        <div className="p-3 border border-indigo-500/30 rounded bg-indigo-500/10 text-indigo-300 font-mono text-[10px]">COGNITION: Compare vs Score -{'>'} Error Calculation</div>
                        <div className="flex justify-center"><Loader2 className="h-4 w-4 text-slate-600 animate-spin" /></div>
                        <div className="p-3 border border-emerald-500/30 rounded bg-emerald-500/10 text-emerald-300 font-mono text-[10px]">ACTION: Servo Movement -{'>'} LED Update -{'>'} MIDI Trigger</div>
                      </div>
                      <div className="mt-8 pt-6 border-t border-slate-800">
                        <p className="text-[10px] text-slate-500 font-mono uppercase tracking-widest">Target Latency: &lt; 20ms</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-12 p-6 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-700 text-white flex items-center justify-between">
                  <div>
                    <h4 className="font-bold">Ready to simulate?</h4>
                    <p className="text-sm opacity-80">Configure these parameters in the next version update.</p>
                  </div>
                  <button className="bg-white text-blue-600 px-6 py-2 rounded-full font-bold text-sm shadow-lg hover:bg-blue-50 transition-colors">View Prototype Docs</button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Demo;