import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Hero from './components/Hero';
import ProjectOverview from './components/ProjectOverview';
import HomeContent from './components/HomeContent';
import Demo from './components/Demo';
import Team from './components/Team';
import Equipment from './components/Equipment';
import Publications from './components/Publications';
import Contact from './components/Contact';
import './App.css';

function Home() {
  return (
    <>
      <Hero />
      <HomeContent />
    </>
  );
}

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/project-overview" element={<ProjectOverview />} />
          <Route path="/team" element={<Team />} />
          <Route path="/equipment" element={<Equipment />} />
          <Route path="/publications" element={<Publications />} />
          <Route path="/demo" element={<Demo />} />
          <Route path="/contact" element={<Contact />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
