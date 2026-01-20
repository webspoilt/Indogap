'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  Rocket,
  Target,
  DollarSign,
  Users,
  Code,
  Calendar,
  CheckCircle,
  ArrowRight,
  Download,
  Share2
} from 'lucide-react'

interface MVPRoadmapProps {
  roadmap: {
    title: string
    targetMarket: string
    pricingStrategy: string
    channels: Array<{ channel: string; strategy: string }>
    techStack: Array<{ layer: string; tech: string }>
    milestones: Array<{ phase: string; tasks: string[] }>
    timeline: string
  }
  onGenerate?: () => void
}

export default function MVPRoadmap({ roadmap, onGenerate }: MVPRoadmapProps) {
  const handleExport = () => {
    // Create markdown content
    const content = `# ${roadmap.title}

## Target Market
${roadmap.targetMarket}

## Pricing Strategy
${roadmap.pricingStrategy}

## Channels
${roadmap.channels.map(c => `### ${c.channel}\n${c.strategy}`).join('\n\n')}

## Tech Stack
${roadmap.techStack.map(t => `### ${t.layer}\n${t.tech}`).join('\n\n')}

## Milestones
${roadmap.milestones.map(m => `### ${m.phase}\n${m.tasks.map(t => `- ${t}`).join('\n')}`).join('\n\n')}

## Timeline
${roadmap.timeline}
`

    // Create and download file
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${roadmap.title.replace(/[^a-z0-9]/gi, '_')}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold mb-2">{roadmap.title}</h2>
          <p className="text-slate-600 dark:text-slate-400">
            AI-generated MVP roadmap tailored for the Indian market
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleExport} className="gap-2">
            <Download className="w-4 h-4" />
            Export
          </Button>
          <Button variant="outline" size="sm" className="gap-2">
            <Share2 className="w-4 h-4" />
            Share
          </Button>
          {onGenerate && (
            <Button size="sm" onClick={onGenerate} className="gap-2">
              <Rocket className="w-4 h-4" />
              Regenerate
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6">
        {/* Target Market */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-emerald-600" />
              Target Market
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="whitespace-pre-line">{roadmap.targetMarket}</p>
            </div>
          </CardContent>
        </Card>

        {/* Pricing Strategy */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-amber-600" />
              Pricing Strategy
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="whitespace-pre-line">{roadmap.pricingStrategy}</p>
            </div>
          </CardContent>
        </Card>

        {/* Channels */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-600" />
              Go-to-Market Channels
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="max-h-96">
              <div className="space-y-4">
                {roadmap.channels.map((channel, index) => (
                  <div key={index} className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
                      <span className="text-sm font-semibold text-blue-600">
                        {index + 1}
                      </span>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold mb-1">{channel.channel}</h4>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {channel.strategy}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Tech Stack */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="w-5 h-5 text-purple-600" />
              Technology Stack
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {roadmap.techStack.map((item, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50"
                >
                  <Badge variant="outline" className="text-xs">
                    {item.layer}
                  </Badge>
                  <span className="text-sm">{item.tech}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-orange-600" />
              Timeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <p className="whitespace-pre-line">{roadmap.timeline}</p>
            </div>
          </CardContent>
        </Card>

        {/* Milestones */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              Development Milestones
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {roadmap.milestones.map((milestone, index) => (
                <div key={index}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center">
                      <span className="font-bold text-emerald-600">
                        {index + 1}
                      </span>
                    </div>
                    <h3 className="font-semibold">{milestone.phase}</h3>
                  </div>
                  <div className="ml-13 space-y-2">
                    {milestone.tasks.map((task, taskIndex) => (
                      <div key={taskIndex} className="flex items-start gap-2">
                        <ArrowRight className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-slate-700 dark:text-slate-300">
                          {task}
                        </span>
                      </div>
                    ))}
                  </div>
                  {index < roadmap.milestones.length - 1 && (
                    <Separator className="my-6" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <Button className="gap-2">
                <Rocket className="w-4 h-4" />
                Start Building MVP
              </Button>
              <Button variant="outline" className="gap-2">
                <Users className="w-4 h-4" />
                Find Co-Founders
              </Button>
              <Button variant="outline" className="gap-2">
                <Target className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
