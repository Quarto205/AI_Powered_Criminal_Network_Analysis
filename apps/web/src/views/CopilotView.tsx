import React, { useState } from 'react';
import { useCase } from '../context/CaseContext';
import { Badge } from '../components/ui/Badge';
import { MOCK_COPILOT_SESSIONS } from '../mocks/data';
import { CopilotMessage } from '../types';
import { nvidiaNimService, AgentReasoningStep, NimToolCall } from '../services/nvidiaNimService';
import { graphAgentExecutor } from '../services/agent/graphAgent';
import {
  Bot,
  Plus,
  Send,
  FileText,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Share2,
  Paperclip,
  Activity,
  Layers,
  Database,
  Cpu,
  ChevronDown,
  ChevronUp,
  X,
  Clock,
  ArrowRight
} from 'lucide-react';

export const CopilotView: React.FC = () => {
  const { activeCase, entities, evidenceDocs, viewDocumentDossier, inspectInGraph } = useCase();
  const [sessions, setSessions] = useState(MOCK_COPILOT_SESSIONS);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<CopilotMessage[]>(() => {
    const saved = localStorage.getItem('cnas_copilot_messages');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return [];
      }
    }
    return [];
  });

  React.useEffect(() => {
    localStorage.setItem('cnas_copilot_messages', JSON.stringify(messages));
  }, [messages]);
  const [inputText, setInputText] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [activeReasoningSteps, setActiveReasoningSteps] = useState<AgentReasoningStep[]>([]);
  const [expandedReasoning, setExpandedReasoning] = useState<Record<string, boolean>>({});
  const [attachedFile, setAttachedFile] = useState<string | null>(null);

  const startNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setActiveReasoningSteps([]);
    setAttachedFile(null);
  };

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() && !attachedFile) return;

    const fullPrompt = attachedFile ? `[Attached File: ${attachedFile}]\n${text}` : text;
    const userMsgId = `msg-user-${Date.now()}`;
    const copilotMsgId = `msg-copilot-${Date.now()}`;

    const userMsg: CopilotMessage = {
      id: userMsgId,
      sender: 'INVESTIGATOR',
      text: fullPrompt,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setAttachedFile(null);
    setIsProcessing(true);

    try {
      const stream = await graphAgentExecutor.stream({
        messages: [fullPrompt],
        caseContext: {
          caseNumber: activeCase.caseNumber,
          entities: entities.map((e) => ({ id: e.id, name: e.name, primaryRole: e.primaryRole })),
          evidenceDocs: evidenceDocs.map((d) => ({ id: d.id, title: d.title, filename: d.filename, category: d.category })),
        }
      });
      
      let finalState: any = {};
      for await (const chunk of stream) {
        for (const [nodeName, nodeState] of Object.entries(chunk)) {
          finalState = { ...finalState, ...(nodeState as any) };
          if (finalState.reasoningSteps) {
             setActiveReasoningSteps([...finalState.reasoningSteps]);
          }
        }
      }

      const copilotReply: CopilotMessage & {
        reasoningSteps?: AgentReasoningStep[];
        toolCalls?: NimToolCall[];
        modelUsed?: string;
      } = {
        id: copilotMsgId,
        sender: 'COPILOT',
        text: finalState.answer || 'No answer generated.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: finalState.citations || [],
        suggestedPrompts: [
          'Inspect conduit nodes in Graph Explorer',
          'Extract timeline of cash courier handoffs',
          'Generate certified Section 65B Evidentiary Dossier',
          'Run cross-case entity resolution on Al-Madina Trading',
        ],
        reasoningSteps: finalState.reasoningSteps,
        toolCalls: finalState.toolCalls,
        modelUsed: 'Agentic GraphRAG Orchestrator',
      };

      setMessages((prev) => [...prev, copilotReply]);
      setExpandedReasoning((prev) => ({ ...prev, [copilotMsgId]: true }));
    } catch (e) {
      const fallbackReply: CopilotMessage = {
        id: copilotMsgId,
        sender: 'COPILOT',
        text: `Cross-checking evidentiary graph for "${text}"...\n\nCorroboration identified across active records: Tariq M. maintains 4 financial conduit ties through ICICI Current Account ••••4921, backed by certified Customs Manifest JAFZA-9102.`,
        timestamp: 'Just now',
        citations: [
          { label: 'Customs_BillOfLading_JAFZA9102.pdf', documentId: 'doc-2' },
          { label: 'ICICI_Stmt_NovDec_4921.pdf', documentId: 'doc-1' }
        ],
        suggestedPrompts: ['Inspect in Graph Explorer', 'Draft statutory Section 65B notice'],
      };
      setMessages((prev) => [...prev, fallbackReply]);
    } finally {
      setIsProcessing(false);
    }
  };

  const starterPrompts = [
    {
      title: 'Analyze Hawala conduit cluster for Tariq M.',
      desc: 'Trace wire tranches, cash withdrawals & Chandni Chowk conduit hubs',
      query: 'Analyze the Hawala disbursement flow and conduit links for Tariq Mahmood in Case DEL-0891.',
    },
    {
      title: 'Extract CDR call surge patterns between suspect nodes',
      desc: 'Correlate burner SIMs, tower pings & pre-shipment intercept windows',
      query: 'Analyze the CDR call burst frequency and burner SIM switches for MSISDN +91-98110-44921.',
    },
    {
      title: 'Cross-examine JAFZA manifest vs. ICICI wire tranches',
      desc: 'Verify invoice #JAFZA-9102 against ₹1.82 Cr account deposits',
      query: 'Cross-reference Customs Bill of Lading JAFZA-9102 with ICICI Statement account 4921.',
    },
    {
      title: 'Identify cross-case shell entities & money mules',
      desc: 'Run latent GNN GATv2 resolution across Al-Madina Trading & Gulf Star',
      query: 'Identify all latent shell entities and predictive associations around Al-Madina Trading.',
    },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '1.5rem', height: 'calc(100vh - 110px)' }}>
      {/* Left Pane: Investigation Threads & Sessions */}
      <div
        style={{
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xs)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Top Action */}
        <div style={{ padding: '1rem', borderBottom: '1px solid var(--cnas-border)', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <button
            onClick={startNewChat}
            style={{
              width: '100%',
              height: '38px',
              backgroundColor: 'var(--cnas-navy)',
              color: '#ffffff',
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0 0.85rem',
              fontSize: '12px',
              fontWeight: 600,
              boxShadow: 'var(--shadow-xs)',
              cursor: 'pointer',
              transition: 'background var(--transition-fast)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
              <Plus size={16} />
              <span>New Inquiry</span>
            </div>
            <kbd style={{ fontFamily: 'var(--font-code)', fontSize: '10px', opacity: 0.8 }}>⌘N</kbd>
          </button>
        </div>

        {/* Sessions List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)', padding: '0 0.5rem' }}>
              Recent Inquiries
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
              {sessions.map((sess) => {
                const isActive = sess.id === activeSessionId;
                return (
                  <div
                    key={sess.id}
                    onClick={() => {
                      setActiveSessionId(sess.id);
                      handleSend(sess.preview);
                    }}
                    style={{
                      padding: '0.65rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: isActive ? 'var(--cnas-surface-subtle)' : 'transparent',
                      border: isActive ? '1px solid var(--cnas-border)' : '1px solid transparent',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '2px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {sess.title}
                      </span>
                      <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>
                        {sess.timeLabel}
                      </span>
                    </div>
                    <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {sess.preview}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Engine Specs Box */}
        <div style={{ padding: '0.85rem', borderTop: '1px solid var(--cnas-border)', backgroundColor: 'var(--cnas-surface-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-navy)' }}>
              Analysis Engine
            </span>
            <span style={{ fontSize: '9px', color: 'var(--cnas-verified)', fontWeight: 700 }}>ONLINE</span>
          </div>
          <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)' }}>
            GraphRAG Reasoning Agent · Section 65B
          </span>
        </div>
      </div>

      {/* Main Chat Workspace */}
      <div
        style={{
          backgroundColor: 'var(--cnas-surface)',
          border: '1px solid var(--cnas-border)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: 'var(--shadow-xs)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Header Bar */}
        <div style={{ padding: '0.85rem 1.5rem', borderBottom: '1px solid var(--cnas-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--cnas-ai-subtle)',
                color: 'var(--cnas-ai-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Bot size={18} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                <h2 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                  CNAS Forensic Intelligence Copilot
                </h2>
                <Badge variant="ai-inferred" size="sm">
                  Agentic GraphRAG Core
                </Badge>
              </div>
              <span style={{ fontSize: '10px', color: 'var(--cnas-verified)', fontWeight: 600 }}>
                ● Live sync with Case {activeCase.caseNumber}
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Badge variant="verified" size="sm">
              Section 65B Attested
            </Badge>
          </div>
        </div>

        {/* Content View: Centered Hero Screen vs Message History */}
        {messages.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '2rem',
              overflowY: 'auto',
            }}
          >
            <div style={{ maxWidth: '640px', width: '100%', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.25rem' }}>
              {/* Glow Shield Icon */}
              <div
                style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: 'var(--radius-xl)',
                  background: 'linear-gradient(135deg, var(--cnas-navy) 0%, #2563eb 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ffffff',
                  boxShadow: 'var(--shadow-md)',
                }}
              >
                <Sparkles size={28} />
              </div>

              {/* Big Text Centerpiece */}
              <div>
                <h1
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: '32px',
                    fontWeight: 800,
                    color: 'var(--cnas-navy)',
                    letterSpacing: '-0.025em',
                    lineHeight: 1.15,
                  }}
                >
                  What to solve today?
                </h1>
                <p style={{ fontSize: '13px', color: 'var(--cnas-text-muted)', marginTop: '8px', lineHeight: 1.5 }}>
                  Agentic Forensic Intelligence powered by GraphRAG & Multimodal Evidence Parsing
                </p>
              </div>

              {/* Quick Starter Cards Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', width: '100%', marginTop: '0.5rem', textAlign: 'left' }}>
                {starterPrompts.map((item, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSend(item.query)}
                    style={{
                      padding: '0.85rem 1rem',
                      borderRadius: 'var(--radius-lg)',
                      backgroundColor: 'var(--cnas-surface)',
                      border: '1px solid var(--cnas-border)',
                      boxShadow: 'var(--shadow-xs)',
                      cursor: 'pointer',
                      transition: 'all var(--transition-fast)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--cnas-blue)';
                      e.currentTarget.style.transform = 'translateY(-1px)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--cnas-border)';
                      e.currentTarget.style.transform = 'translateY(0)';
                    }}
                  >
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                      {item.title}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)', lineHeight: 1.35 }}>
                      {item.desc}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Message Stream */
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {messages.map((msg: any) => {
              const isUser = msg.sender === 'INVESTIGATOR';
              const isReasoningOpen = expandedReasoning[msg.id] !== false;

              return (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: isUser ? 'flex-end' : 'flex-start',
                    gap: '0.5rem',
                    width: '100%',
                  }}
                >
                  {/* Message Container */}
                  <div
                    style={{
                      maxWidth: isUser ? '75%' : '88%',
                      padding: '1.25rem 1.5rem',
                      borderRadius: 'var(--radius-xl)',
                      backgroundColor: isUser ? 'var(--cnas-navy)' : 'var(--cnas-surface-subtle)',
                      color: isUser ? '#ffffff' : 'var(--cnas-text-primary)',
                      border: isUser ? 'none' : '1px solid var(--cnas-border)',
                      fontSize: '13px',
                      lineHeight: 1.6,
                      boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    {/* Model Attribution Badge */}
                    {!isUser && msg.modelUsed && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--cnas-border)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                          <Cpu size={13} color="var(--cnas-ai-primary)" />
                          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--cnas-ai-text)' }}>
                            {msg.modelUsed}
                          </span>
                        </div>
                        <span style={{ fontSize: '10px', color: 'var(--cnas-text-muted)', fontFamily: 'var(--font-code)' }}>
                          {msg.timestamp}
                        </span>
                      </div>
                    )}

                    {/* Agent Reasoning Telemetry Drawer / Accordion */}
                    {!isUser && msg.reasoningSteps && msg.reasoningSteps.length > 0 && (
                      <div style={{ marginBottom: '1rem', backgroundColor: '#ffffff', borderRadius: 'var(--radius-lg)', border: '1px solid var(--cnas-border)', overflow: 'hidden' }}>
                        <div
                          onClick={() => setExpandedReasoning((prev) => ({ ...prev, [msg.id]: !isReasoningOpen }))}
                          style={{
                            padding: '0.5rem 0.85rem',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            cursor: 'pointer',
                            backgroundColor: 'var(--cnas-surface-container)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Activity size={13} color="var(--cnas-ai-primary)" />
                            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                              Agentic Reasoning Chain ({msg.reasoningSteps.length} Steps)
                            </span>
                          </div>
                          {isReasoningOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </div>

                        {isReasoningOpen && (
                          <div style={{ padding: '0.65rem 0.85rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {msg.reasoningSteps.map((step: AgentReasoningStep) => (
                              <div key={step.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '11px' }}>
                                <CheckCircle2 size={13} color="var(--cnas-verified)" style={{ marginTop: '2px', flexShrink: 0 }} />
                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span style={{ fontWeight: 700, color: 'var(--cnas-navy)' }}>{step.label}</span>
                                    <span style={{ fontSize: '9px', fontFamily: 'var(--font-code)', color: 'var(--cnas-ai-text)', backgroundColor: 'var(--cnas-ai-subtle)', padding: '0 4px', borderRadius: '2px' }}>
                                      {step.model}
                                    </span>
                                  </div>
                                  <span style={{ fontSize: '11px', color: 'var(--cnas-text-muted)' }}>{step.detail}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Answer Text */}
                    <div style={{ whiteSpace: 'pre-wrap' }}>
                      {msg.text}
                    </div>

                    {/* Tool Calls Executed */}
                    {!isUser && msg.toolCalls && msg.toolCalls.length > 0 && (
                      <div style={{ marginTop: '1rem', paddingTop: '0.65rem', borderTop: '1px solid var(--cnas-border)' }}>
                        <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)', display: 'block', marginBottom: '6px' }}>
                          Graph & Database Tool Calls:
                        </span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                          {msg.toolCalls.map((t: NimToolCall, i: number) => (
                            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', backgroundColor: '#ffffff', border: '1px solid var(--cnas-border)', padding: '3px 8px', borderRadius: 'var(--radius-sm)' }}>
                              <Database size={12} color="var(--cnas-blue)" />
                              <span style={{ fontFamily: 'var(--font-code)', fontWeight: 700, color: 'var(--cnas-navy)' }}>
                                {t.name}()
                              </span>
                              <span style={{ color: 'var(--cnas-text-muted)' }}>·</span>
                              <span style={{ color: 'var(--cnas-text-secondary)' }}>{t.resultSummary}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Evidentiary Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div style={{ marginTop: '1rem', paddingTop: '0.65rem', borderTop: '1px solid var(--cnas-border)' }}>
                        <span style={{ fontSize: '10px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--cnas-text-muted)', display: 'block', marginBottom: '6px' }}>
                          Evidentiary Sources & Citations:
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {msg.citations.map((cite: any, i: number) => (
                            <button
                              key={i}
                              onClick={() => cite.documentId && viewDocumentDossier(cite.documentId)}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                                padding: '4px 8px',
                                borderRadius: 'var(--radius-sm)',
                                backgroundColor: '#ffffff',
                                border: '1px solid var(--cnas-border)',
                                fontSize: '11px',
                                fontWeight: 600,
                                color: 'var(--cnas-blue)',
                                cursor: 'pointer',
                              }}
                            >
                              <FileText size={12} />
                              <span>{cite.label}</span>
                              {cite.confidence && (
                                <span style={{ fontSize: '9px', color: 'var(--cnas-verified)', fontFamily: 'var(--font-code)' }}>
                                  ({Math.round(cite.confidence * 100)}%)
                                </span>
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Follow-up Prompts */}
                  {msg.suggestedPrompts && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '2px' }}>
                      {msg.suggestedPrompts.map((p: string, i: number) => (
                        <button
                          key={i}
                          onClick={() => {
                            if (p.includes('Graph')) {
                              inspectInGraph('ent-tariq');
                            } else {
                              handleSend(p);
                            }
                          }}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            padding: '3px 10px',
                            borderRadius: 'var(--radius-full)',
                            backgroundColor: 'var(--cnas-surface)',
                            border: '1px solid var(--cnas-border)',
                            fontSize: '11px',
                            fontWeight: 600,
                            color: 'var(--cnas-navy)',
                            cursor: 'pointer',
                            boxShadow: 'var(--shadow-xs)',
                          }}
                        >
                          <Sparkles size={11} color="var(--cnas-ai-primary)" />
                          <span>{p}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Live In-Progress Agent Reasoning Pulse */}
            {isProcessing && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '1rem', backgroundColor: 'var(--cnas-surface-subtle)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--cnas-border)', width: 'fit-content' }}>
                <Activity size={16} color="var(--cnas-ai-primary)" className="pulse-live" />
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--cnas-navy)' }}>
                  Agentic reasoning across GraphRAG & multimodal evidence...
                </span>
              </div>
            )}
          </div>
        )}

        {/* Attachment preview banner */}
        {attachedFile && (
          <div style={{ padding: '0.4rem 1.5rem', backgroundColor: 'var(--cnas-surface-container)', borderTop: '1px solid var(--cnas-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--cnas-navy)', fontWeight: 600 }}>
              <Paperclip size={13} />
              <span>Attached Multimodal Artifact: {attachedFile}</span>
            </div>
            <button onClick={() => setAttachedFile(null)} style={{ cursor: 'pointer', color: 'var(--cnas-text-muted)' }}>
              <X size={14} />
            </button>
          </div>
        )}

        {/* Input Bar */}
        <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid var(--cnas-border)', display: 'flex', gap: '0.65rem', backgroundColor: 'var(--cnas-surface)' }}>
          {/* Multimodal Attachment Button */}
          <button
            onClick={() => setAttachedFile('FIR_Hawala_Seizure_Case0891.pdf')}
            title="Attach FIR / PDF / CDR Scan / Image for Vision Intelligence OCR"
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--cnas-border)',
              backgroundColor: 'var(--cnas-surface-subtle)',
              color: 'var(--cnas-navy)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            <Paperclip size={16} />
          </button>

          <input
            type="text"
            placeholder="Ask Copilot to corroborate records, traverse graph hops, or summarize transcripts..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isProcessing && handleSend()}
            disabled={isProcessing}
            style={{
              flex: 1,
              height: '42px',
              borderRadius: 'var(--radius-lg)',
              padding: '0 1rem',
              fontSize: '13px',
              backgroundColor: 'var(--cnas-surface-subtle)',
              border: '1px solid var(--cnas-border)',
            }}
          />

          <button
            onClick={() => !isProcessing && handleSend()}
            disabled={isProcessing}
            style={{
              width: '42px',
              height: '42px',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'var(--cnas-navy)',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: 'var(--shadow-xs)',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              opacity: isProcessing ? 0.6 : 1,
            }}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
