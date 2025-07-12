import { useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { ThumbsUp, ThumbsDown, MessageCircle, Zap, User, ArrowLeft, Send, Bot } from "lucide-react";
import { api, type Question, type Answer } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const QuestionDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();
  const [newAnswer, setNewAnswer] = useState("");
  const [showAIAnswer, setShowAIAnswer] = useState(false);

  // Fetch question data
  const { data: question, isLoading: questionLoading, error: questionError } = useQuery({
    queryKey: ['question', id],
    queryFn: () => api.getQuestion(id!),
    enabled: !!id,
  });

  // Fetch answers for this question
  const { data: answers = [], isLoading: answersLoading, refetch: refetchAnswers } = useQuery({
    queryKey: ['answers', id],
    queryFn: () => api.getAnswers(id!),
    enabled: !!id,
  });

  // Create answer mutation
  const createAnswerMutation = useMutation({
    mutationFn: (content: string) => api.createAnswer(id!, { content }),
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Answer posted successfully!",
      });
      setNewAnswer("");
      refetchAnswers();
    },
    onError: (error) => {
      let errorMessage = "Failed to post answer";
      
      // Handle specific error cases
      if (error.message.includes("community guidelines")) {
        errorMessage = error.message;
      } else if (error.message.includes("authentication")) {
        errorMessage = "Please log in to post an answer";
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });

  // AI answer generation mutation
  const generateAIAnswerMutation = useMutation({
    mutationFn: () => api.generateAIAnswer(id!),
    onSuccess: (aiAnswer) => {
      toast({
        title: "Success",
        description: "AI answer generated and posted successfully!",
      });
      setShowAIAnswer(true);
      refetchAnswers(); // Refresh to show the new AI answer
    },
    onError: (error) => {
      let errorMessage = "Failed to generate AI answer";
      
      if (error.message.includes("authentication")) {
        errorMessage = "Please log in to generate AI answers";
      } else if (error.message.includes("unavailable")) {
        errorMessage = "AI answer generation is currently unavailable. Please try again later.";
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      });
    },
  });

  const aiAnswer = `Based on your question about implementing React Context with TypeScript, here's a comprehensive solution:

**1. Define Your Context Type Interface**
First, create a clear interface for your context:

\`\`\`typescript
interface AppContextType {
  user: User | null;
  theme: 'light' | 'dark';
  setUser: (user: User | null) => void;
  toggleTheme: () => void;
}
\`\`\`

**2. Create the Context with Default Value**
\`\`\`typescript
const AppContext = createContext<AppContextType | undefined>(undefined);
\`\`\`

**3. Custom Hook for Type Safety**
\`\`\`typescript
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};
\`\`\`

**4. Provider Component**
\`\`\`typescript
export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  const value: AppContextType = {
    user,
    theme,
    setUser,
    toggleTheme
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
\`\`\`

This pattern ensures full type safety and prevents runtime errors from undefined context usage.`;

  const handleSubmitAnswer = () => {
    if (newAnswer.trim()) {
      createAnswerMutation.mutate(newAnswer.trim());
    }
  };

  // Loading state
  if (questionLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center py-12">
              <p>Loading question...</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Error state
  if (questionError || !question) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-center py-12">
              <h3 className="text-lg font-semibold mb-2">Question not found</h3>
              <p className="text-muted-foreground mb-4">The question you're looking for doesn't exist or has been removed.</p>
              <Button onClick={() => window.history.back()}>
                Go Back
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Back button */}
          <Button variant="ghost" className="mb-6" onClick={() => window.history.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Questions
          </Button>

          {/* Question */}
          <Card className="p-8 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                <User className="w-4 h-4" />
                <span>{question.username || 'Anonymous'}</span>
                <span>•</span>
                <span>{new Date(question.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            <h1 className="text-2xl font-poppins font-bold text-foreground mb-4">
              {question.title}
            </h1>

            <div className="prose prose-gray max-w-none mb-6">
              <p className="text-foreground leading-relaxed whitespace-pre-line">
                {question.description}
              </p>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-2 mb-6">
              {question.tags.map((tag, index) => (
                <Badge 
                  key={index} 
                  variant="secondary" 
                  className="bg-primary/10 text-primary hover:bg-primary/20 border-primary/20"
                >
                  {tag}
                </Badge>
              ))}
            </div>

            {/* Question Actions */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Button variant="like" size="sm">
                  <ThumbsUp className="w-4 h-4 mr-1" />
                  0
                </Button>
                <Button variant="dislike" size="sm">
                  <ThumbsDown className="w-4 h-4 mr-1" />
                  0
                </Button>
                <div className="flex items-center text-muted-foreground">
                  <MessageCircle className="w-4 h-4 mr-1" />
                  <span className="text-sm">{question.answer_count} answers</span>
                </div>
              </div>

              <Button 
                variant="secondary" 
                size="sm" 
                onClick={() => {
                  if (!api.isAuthenticated()) {
                    toast({
                      title: "Authentication Required",
                      description: "Please log in to generate AI answers",
                      variant: "destructive",
                    });
                    return;
                  }
                  generateAIAnswerMutation.mutate();
                }}
                disabled={generateAIAnswerMutation.isPending}
              >
                <Zap className="w-4 h-4 mr-1" />
                {generateAIAnswerMutation.isPending ? "Generating..." : "Ask AI"}
              </Button>
            </div>
          </Card>

          {/* AI Answer */}
          {showAIAnswer && (
            <Card className="p-6 mb-6 bg-gradient-to-r from-primary/5 to-secondary/5 border-primary/20">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="font-poppins font-semibold text-foreground">AI Generated Answer</h3>
                  <p className="text-xs text-muted-foreground">Generated by AI • Always verify with official documentation</p>
                </div>
              </div>
              <div className="prose prose-gray max-w-none">
                <div className="text-foreground leading-relaxed whitespace-pre-line">
                  {aiAnswer}
                </div>
              </div>
            </Card>
          )}

          {/* Answers Section */}
          <div className="mb-8">
            <h2 className="text-xl font-poppins font-bold text-foreground mb-4">
              {answers.length} Answers
            </h2>

            {answersLoading ? (
              <div className="text-center py-8">
                <p>Loading answers...</p>
              </div>
            ) : answers.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No answers yet. Be the first to answer!</p>
              </div>
            ) : (
              <div className="space-y-6">
                {answers.map((answer) => (
                  <Card key={answer.id} className={`p-6 ${answer.is_accepted ? 'border-success bg-success/5' : ''}`}>
                    {answer.is_accepted && (
                      <div className="flex items-center space-x-2 mb-3">
                        <ThumbsUp className="w-4 h-4 text-success" />
                        <span className="text-sm font-medium text-success">Accepted Answer</span>
                      </div>
                    )}

                    <div className="flex items-center space-x-2 text-sm text-muted-foreground mb-4">
                      <User className="w-4 h-4" />
                      <span>{answer.username || 'Anonymous'}</span>
                      <span>•</span>
                      <span>{new Date(answer.created_at).toLocaleDateString()}</span>
                    </div>

                    <div className="prose prose-gray max-w-none mb-4">
                      <div className="text-foreground leading-relaxed whitespace-pre-line">
                        {answer.content}
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <Button variant="like" size="sm">
                        <ThumbsUp className="w-4 h-4 mr-1" />
                        {answer.votes}
                      </Button>
                      <Button variant="dislike" size="sm">
                        <ThumbsDown className="w-4 h-4 mr-1" />
                        0
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Answer Form */}
          <Card className="p-6">
            <h3 className="text-lg font-poppins font-semibold text-foreground mb-4">
              Your Answer
            </h3>
            <div className="space-y-4">
              <Textarea
                placeholder="Write your answer here... Be sure to answer the question. Provide details and share your research!"
                value={newAnswer}
                onChange={(e) => setNewAnswer(e.target.value)}
                className="min-h-[150px]"
              />
              <div className="flex justify-end">
                <Button 
                  variant="hero" 
                  onClick={handleSubmitAnswer}
                  disabled={!newAnswer.trim() || createAnswerMutation.isPending}
                >
                  <Send className="w-4 h-4 mr-2" />
                  {createAnswerMutation.isPending ? "Posting..." : "Post Answer"}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default QuestionDetail;