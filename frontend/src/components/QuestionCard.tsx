import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThumbsUp, ThumbsDown, MessageCircle, Zap, User } from "lucide-react";

interface Question {
  id: string;
  title: string;
  description: string;
  tags: string[];
  likes: number;
  dislikes: number;
  answers: number;
  author: string;
  timestamp: string;
  isLiked?: boolean;
  isDisliked?: boolean;
}

interface QuestionCardProps {
  question: Question;
  onLike?: () => void;
  onDislike?: () => void;
  onAnswer?: () => void;
  onAskAI?: () => void;
}

export const QuestionCard = ({ 
  question, 
  onLike, 
  onDislike, 
  onAnswer, 
  onAskAI 
}: QuestionCardProps) => {
  return (
    <div className="bg-card border border-border rounded-xl p-6 shadow-card hover:shadow-elevated transition-all duration-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
          <User className="w-4 h-4" />
          <span>{question.author}</span>
          <span>•</span>
          <span>{question.timestamp}</span>
        </div>
      </div>

      {/* Content */}
      <div className="mb-4">
        <h3 className="text-lg font-poppins font-semibold text-foreground mb-2 hover:text-primary cursor-pointer transition-colors">
          {question.title}
        </h3>
        <p className="text-muted-foreground line-clamp-3 leading-relaxed">
          {question.description}
        </p>
      </div>

      {/* Tags */}
      {question.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
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
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {/* Like/Dislike */}
          <div className="flex items-center space-x-1">
            <Button
              variant={question.isLiked ? "success" : "like"}
              size="sm"
              onClick={onLike}
              className="px-3"
            >
              <ThumbsUp className="w-4 h-4 mr-1" />
              {question.likes}
            </Button>
            <Button
              variant={question.isDisliked ? "destructive" : "dislike"}
              size="sm"
              onClick={onDislike}
              className="px-3"
            >
              <ThumbsDown className="w-4 h-4 mr-1" />
              {question.dislikes}
            </Button>
          </div>

          {/* Answers count */}
          <div className="flex items-center text-muted-foreground">
            <MessageCircle className="w-4 h-4 mr-1" />
            <span className="text-sm">{question.answers} answers</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={onAnswer}>
            <MessageCircle className="w-4 h-4 mr-1" />
            Answer
          </Button>
          <Button variant="secondary" size="sm" onClick={onAskAI}>
            <Zap className="w-4 h-4 mr-1" />
            Ask AI
          </Button>
        </div>
      </div>
    </div>
  );
};