import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Tag, X, MessageSquarePlus, Lightbulb } from "lucide-react";
import { api, type QuestionCreate } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const AskQuestion = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");

  // Create question mutation
  const createQuestionMutation = useMutation({
    mutationFn: api.createQuestion,
    onSuccess: () => {
      toast({
        title: "Success",
        description: "Question posted successfully!",
      });
      navigate("/");
    },
    onError: (error) => {
      console.error("Question creation error:", error);
      if (error.message.includes("401") || error.message.includes("authentication")) {
        toast({
          title: "Authentication Required",
          description: "Please log in to post a question.",
          variant: "destructive",
        });
        navigate("/login");
      } else {
        toast({
          title: "Error",
          description: error.message || "Failed to post question. Please try again.",
          variant: "destructive",
        });
      }
    },
  });

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim()) && tags.length < 5) {
      setTags([...tags, tagInput.trim()]);
      setTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleSubmit = () => {
    if (title.trim() && description.trim() && description.length >= 30) {
      const questionData: QuestionCreate = {
        title: title.trim(),
        description: description.trim(),
        tags: tags
      };
      
      createQuestionMutation.mutate(questionData);
    }
  };

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

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main Form */}
            <div className="lg:col-span-2">
              <Card className="p-8">
                <div className="flex items-center space-x-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center">
                    <MessageSquarePlus className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-poppins font-bold text-foreground">
                      Ask a Question
                    </h1>
                    <p className="text-muted-foreground">
                      Get help from the community
                    </p>
                  </div>
                </div>

                <div className="space-y-6">
                  {/* Title */}
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Question Title *
                    </label>
                    <Input
                      placeholder="Be specific and imagine you're asking a question to another person"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      className="text-base"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      {title.length}/150 characters
                    </p>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Question Details *
                    </label>
                    <Textarea
                      placeholder="Provide all the details. What exactly are you trying to do? What have you tried? What's the expected result?"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="min-h-[200px] text-base"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Minimum 30 characters ({description.length}/30)
                    </p>
                  </div>

                  {/* Tags */}
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Tags
                    </label>
                    <div className="flex items-center space-x-2 mb-3">
                      <Tag className="w-4 h-4 text-muted-foreground" />
                      <Input
                        placeholder="Add up to 5 tags to categorize your question"
                        value={tagInput}
                        onChange={(e) => setTagInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        className="flex-1"
                        disabled={tags.length >= 5}
                      />
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={handleAddTag}
                        disabled={!tagInput.trim() || tags.length >= 5}
                      >
                        Add
                      </Button>
                    </div>
                    
                    {tags.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-2">
                        {tags.map((tag, index) => (
                          <Badge 
                            key={index} 
                            variant="secondary"
                            className="bg-primary/10 text-primary hover:bg-primary/20 border-primary/20"
                          >
                            {tag}
                            <button
                              onClick={() => handleRemoveTag(tag)}
                              className="ml-2 hover:text-destructive"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Tags help others find and answer your question
                    </p>
                  </div>

                  {/* Submit */}
                  <div className="flex justify-end space-x-3 pt-4">
                    <Button 
                      variant="outline" 
                      onClick={() => window.history.back()}
                    >
                      Cancel
                    </Button>
                    <Button 
                      variant="hero" 
                      onClick={handleSubmit}
                      disabled={!title.trim() || description.length < 30 || createQuestionMutation.isPending}
                    >
                      <MessageSquarePlus className="w-4 h-4 mr-2" />
                      {createQuestionMutation.isPending ? "Posting..." : "Post Question"}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>

            {/* Sidebar Tips */}
            <div className="space-y-6">
              <Card className="p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <Lightbulb className="w-5 h-5 text-primary" />
                  <h3 className="font-poppins font-semibold text-foreground">
                    Writing Tips
                  </h3>
                </div>
                <div className="space-y-3 text-sm text-muted-foreground">
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Be Specific</h4>
                    <p>Include exact error messages, code snippets, and expected behavior.</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Show Research</h4>
                    <p>Mention what you've already tried and searched for.</p>
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Use Tags</h4>
                    <p>Add relevant technologies, frameworks, and programming languages.</p>
                  </div>
                </div>
              </Card>

              <Card className="p-6">
                <h3 className="font-poppins font-semibold text-foreground mb-3">
                  Popular Tags
                </h3>
                <div className="flex flex-wrap gap-2">
                  {['React', 'JavaScript', 'Python', 'Node.js', 'TypeScript', 'CSS'].map((tag) => (
                    <Badge 
                      key={tag}
                      variant="outline"
                      className="cursor-pointer hover:bg-primary/10"
                      onClick={() => {
                        if (!tags.includes(tag) && tags.length < 5) {
                          setTags([...tags, tag]);
                        }
                      }}
                    >
                      {tag}
                    </Badge>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AskQuestion;