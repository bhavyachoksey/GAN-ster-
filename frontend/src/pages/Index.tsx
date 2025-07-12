import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { QuestionCard } from "@/components/QuestionCard";
import { AskQuestionCard } from "@/components/AskQuestionCard";
import { api, type Question } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { TrendingUp, Clock, ThumbsUp, MessageSquarePlus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const Index = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [sortBy, setSortBy] = useState<"trending" | "recent" | "popular">("recent");

  // Fetch questions from API
  const { data: questions = [], isLoading, error, refetch } = useQuery({
    queryKey: ['questions'],
    queryFn: () => api.getQuestions(0, 50),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  useEffect(() => {
    if (error) {
      toast({
        title: "Error",
        description: "Failed to load questions. Please try again.",
        variant: "destructive",
      });
    }
  }, [error, toast]);

  const handleAnswer = (questionId: string) => {
    navigate(`/question/${questionId}`);
  };

  const handleAskAI = (questionId: string) => {
    navigate(`/question/${questionId}#ai-answer`);
  };

  // Convert API questions to frontend format for compatibility
  const convertedQuestions = questions.map((q): Question & { likes: number; dislikes: number; answers: number; author: string; timestamp: string; isLiked?: boolean; isDisliked?: boolean } => ({
    ...q,
    likes: q.answer_count * 2, // Mock likes based on activity
    dislikes: 0, // Backend doesn't have dislikes yet
    answers: q.answer_count,
    author: q.username || 'Anonymous',
    timestamp: new Date(q.created_at).toLocaleDateString(),
    isLiked: false,
    isDisliked: false,
  }));

  const sortedQuestions = [...convertedQuestions].sort((a, b) => {
    switch (sortBy) {
      case "recent":
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case "popular":
        return b.answer_count - a.answer_count;
      default: // trending
        return (b.answer_count + b.likes) - (a.answer_count + a.likes);
    }
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto space-y-6">
            <AskQuestionCard />
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-pulse">Loading questions...</div>
              </div>
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
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Ask Question Card */}
          <AskQuestionCard />

          {/* Filter Buttons */}
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-poppins font-bold text-foreground">
              Questions ({questions.length})
            </h2>
            <div className="flex items-center space-x-2">
              <Button
                variant={sortBy === "trending" ? "default" : "outline"}
                size="sm"
                onClick={() => setSortBy("trending")}
              >
                <TrendingUp className="w-4 h-4 mr-1" />
                Trending
              </Button>
              <Button
                variant={sortBy === "recent" ? "default" : "outline"}
                size="sm"
                onClick={() => setSortBy("recent")}
              >
                <Clock className="w-4 h-4 mr-1" />
                Recent
              </Button>
              <Button
                variant={sortBy === "popular" ? "default" : "outline"}
                size="sm"
                onClick={() => setSortBy("popular")}
              >
                <ThumbsUp className="w-4 h-4 mr-1" />
                Popular
              </Button>
            </div>
          </div>

          {/* Questions Feed */}
          <div className="space-y-4">
            {sortedQuestions.length === 0 ? (
              <div className="text-center py-12">
                <h3 className="text-lg font-semibold mb-2">No questions yet</h3>
                <p className="text-muted-foreground mb-4">Be the first to ask a question!</p>
                <Button onClick={() => navigate('/ask')}>
                  Ask the First Question
                </Button>
              </div>
            ) : (
              sortedQuestions.map((question) => (
                <QuestionCard
                  key={question.id}
                  question={question}
                  onLike={() => {}} // Placeholder - backend doesn't support likes yet
                  onDislike={() => {}} // Placeholder - backend doesn't support dislikes yet
                  onAnswer={() => handleAnswer(question.id)}
                  onAskAI={() => handleAskAI(question.id)}
                />
              ))
            )}
          </div>

          {/* Refresh Button */}
          <div className="text-center pt-8">
            <Button 
              variant="outline" 
              size="lg"
              onClick={() => refetch()}
              disabled={isLoading}
            >
              {isLoading ? "Loading..." : "Refresh Questions"}
            </Button>
          </div>
        </div>
      </main>

      {/* Floating Action Button for Mobile */}
      <button 
        className="fab sm:hidden"
        onClick={() => navigate('/ask')}
      >
        <MessageSquarePlus className="w-6 h-6" />
      </button>
    </div>
  );
};

export default Index;
