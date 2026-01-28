'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { PageLoadingSkeleton, OpportunityCardSkeleton } from '@/components/ui/skeleton'
import { ThemeToggle } from '@/components/ui/theme-toggle'
import { ErrorBoundary } from '@/components/ui/error-boundary'
import MVPRoadmap from '@/components/opportunity/MVPRoadmap'
import {
  TrendingUp,
  Target,
  Globe,
  MapPin,
  DollarSign,
  Clock,
  AlertCircle,
  CheckCircle,
  Zap,
  BarChart3,
  Plus,
  Search,
  Filter,
  Star,
  ExternalLink,
  Building2,
  Rocket,
  Lightbulb,
  Download
} from 'lucide-react'

interface Opportunity {
  id: string
  title: string
  description: string
  globalSource: string
  globalReference: string
  successScore: number
  status: string
  indianCompetitors?: string
  gapAnalysis?: string
  culturalFit?: number
  logisticsComplexity?: number
  paymentReadiness?: number
  timingAlignment?: number
  monopolyPotential?: number
  regulatoryRisk?: number
  executionFeasibility?: number
  notes?: string
  createdAt: string
}

interface IndianStartup {
  id: string
  name: string
  description: string
  category: string
  website?: string
}

export default function OpportunityEngine() {
  const [activeTab, setActiveTab] = useState('opportunities')
  const [loading, setLoading] = useState(true)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [indianStartups, setIndianStartups] = useState<IndianStartup[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterSource, setFilterSource] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterMinScore, setFilterMinScore] = useState(0)
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null)
  const [isAddStartupOpen, setIsAddStartupOpen] = useState(false)
  const [newStartup, setNewStartup] = useState({
    name: '',
    description: '',
    category: '',
    website: ''
  })
  const [isAnalyzeOpen, setIsAnalyzeOpen] = useState(false)
  const [analyzeUrl, setAnalyzeUrl] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [generatingMVP, setGeneratingMVP] = useState(false)
  const [selectedMVP, setSelectedMVP] = useState<any>(null)

  // Fetch data from APIs
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [oppsRes, startupsRes] = await Promise.all([
          fetch('/api/opportunities'),
          fetch('/api/indian-startups')
        ])

        if (oppsRes.ok) {
          const data = await oppsRes.json()
          setOpportunities(data)
        }

        if (startupsRes.ok) {
          const data = await startupsRes.json()
          setIndianStartups(data)
        }
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const filteredOpportunities = opportunities.filter(opp => {
    const matchesSearch = opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      opp.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesSource = filterSource === 'all' || opp.globalSource === filterSource
    const matchesStatus = filterStatus === 'all' || opp.status === filterStatus
    const matchesScore = opp.successScore >= filterMinScore

    return matchesSearch && matchesSource && matchesStatus && matchesScore
  })

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-emerald-600'
    if (score >= 50) return 'text-amber-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (score: number) => {
    if (score >= 75) return 'bg-emerald-100 dark:bg-emerald-900/20'
    if (score >= 50) return 'bg-amber-100 dark:bg-amber-900/20'
    return 'bg-red-100 dark:bg-red-900/20'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'New': return 'bg-blue-500'
      case 'Validating': return 'bg-purple-500'
      case 'Building': return 'bg-orange-500'
      case 'Sold': return 'bg-green-500'
      case 'Declined': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const calculateStats = () => {
    const total = opportunities.length
    const highPotential = opportunities.filter(o => o.successScore >= 75).length
    const avgScore = Math.round(opportunities.reduce((sum, o) => sum + o.successScore, 0) / total)
    const bySource = opportunities.reduce((acc, o) => {
      acc[o.globalSource] = (acc[o.globalSource] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return { total, highPotential, avgScore, bySource }
  }

  const stats = calculateStats()

  const handleAddStartup = async () => {
    if (newStartup.name && newStartup.description && newStartup.category) {
      try {
        const response = await fetch('/api/indian-startups', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newStartup)
        })

        if (response.ok) {
          const addedStartup = await response.json()
          setIndianStartups([...indianStartups, addedStartup])
          setNewStartup({ name: '', description: '', category: '', website: '' })
          setIsAddStartupOpen(false)
        }
      } catch (error) {
        console.error('Error adding startup:', error)
      }
    }
  }

  const handleAnalyzeUrl = async () => {
    if (!analyzeUrl) return

    setAnalyzing(true)
    try {
      const response = await fetch('/api/analyze-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: analyzeUrl })
      })

      if (response.ok) {
        const newOpportunity = await response.json()
        setOpportunities([newOpportunity, ...opportunities])
        setIsAnalyzeOpen(false)
        setAnalyzeUrl('')
      }
    } catch (error) {
      console.error('Error analyzing URL:', error)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleGenerateMVP = async (opportunity: Opportunity) => {
    setGeneratingMVP(true)
    setSelectedMVP(null)

    try {
      const response = await fetch('/api/generate-mvp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ opportunityId: opportunity.id })
      })

      if (response.ok) {
        const roadmap = await response.json()
        setSelectedMVP(roadmap)
        setSelectedOpportunity(null)
        setActiveTab('mvp-generator')
      }
    } catch (error) {
      console.error('Error generating MVP:', error)
    } finally {
      setGeneratingMVP(false)
    }
  }

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      // In production, this would call the export API
      // For now, we'll create a client-side export

      const exportData = filteredOpportunities.map(opp => ({
        ID: opp.id,
        Title: opp.title,
        Description: opp.description,
        Source: opp.globalSource,
        Reference: opp.globalReference,
        SuccessScore: opp.successScore,
        Status: opp.status,
        CulturalFit: opp.culturalFit,
        LogisticsComplexity: opp.logisticsComplexity,
        PaymentReadiness: opp.paymentReadiness,
        TimingAlignment: opp.timingAlignment,
        MonopolyPotential: opp.monopolyPotential,
        RegulatoryRisk: opp.regulatoryRisk,
        ExecutionFeasibility: opp.executionFeasibility,
        IndianCompetitors: opp.indianCompetitors,
        GapAnalysis: opp.gapAnalysis,
        Notes: opp.notes,
        CreatedAt: opp.createdAt
      }))

      if (format === 'json') {
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `opportunities-${Date.now()}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } else {
        // CSV export
        const headers = Object.keys(exportData[0]).join(',')
        const rows = exportData.map(row =>
          Object.values(row).map(val =>
            typeof val === 'string' ? `"${val.replace(/"/g, '""')}"` : val
          ).join(',')
        )
        const csv = [headers, ...rows].join('\n')
        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `opportunities-${Date.now()}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
    } catch (error) {
      console.error('Error exporting opportunities:', error)
    }
  }

  // Show loading skeleton while data is loading
  if (loading) {
    return <PageLoadingSkeleton />
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
        {/* Header */}
        <header className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
                    Opportunity Discovery Engine
                  </h1>
                  <p className="text-sm text-slate-700 dark:text-slate-300">
                    AI-Powered Market Intelligence for India
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Dialog open={isAnalyzeOpen} onOpenChange={setIsAnalyzeOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" size="sm" className="gap-2">
                      <Search className="w-4 h-4" />
                      Analyze URL
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Analyze Global Opportunity</DialogTitle>
                      <DialogDescription>
                        Paste a URL from YC, Product Hunt, or any global startup to analyze it for the Indian market.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <Label>URL</Label>
                        <Input
                          placeholder="https://www.ycombinator.com/companies/..."
                          value={analyzeUrl}
                          onChange={(e) => setAnalyzeUrl(e.target.value)}
                        />
                      </div>
                      <Button
                        onClick={handleAnalyzeUrl}
                        disabled={!analyzeUrl || analyzing}
                        className="w-full"
                      >
                        {analyzing ? 'Analyzing...' : 'Analyze Opportunity'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
                <ThemeToggle />
                <Button size="sm" className="gap-2 bg-emerald-600 hover:bg-emerald-700">
                  <Plus className="w-4 h-4" />
                  Add Opportunity
                </Button>
              </div>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-6" role="main" aria-label="Main content">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Opportunities</CardTitle>
                <BarChart3 className="h-4 w-4 text-slate-700 dark:text-slate-300" aria-hidden="true" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total}</div>
                <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                  Discovered opportunities
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">High Potential</CardTitle>
                <Star className="h-4 w-4 text-amber-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.highPotential}</div>
                <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                  Score ≥ 75%
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Average Score</CardTitle>
                <TrendingUp className="h-4 w-4 text-emerald-600" />
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${getScoreColor(stats.avgScore)}`}>
                  {stats.avgScore}%
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                  Success probability
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Indian Startups</CardTitle>
                <Building2 className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{indianStartups.length}</div>
                <p className="text-xs text-slate-700 dark:text-slate-300 mt-1">
                  In knowledge graph
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Main Content Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="opportunities" className="gap-2">
                <Target className="w-4 h-4" />
                Opportunities
              </TabsTrigger>
              <TabsTrigger value="knowledge-graph" className="gap-2">
                <MapPin className="w-4 h-4" />
                Knowledge Graph
              </TabsTrigger>
              <TabsTrigger value="mvp-generator" className="gap-2">
                <Rocket className="w-4 h-4" />
                MVP Generator
              </TabsTrigger>
            </TabsList>

            {/* Opportunities Tab */}
            <TabsContent value="opportunities" className="space-y-4">
              {/* Filters */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <Filter className="w-5 h-5" />
                      Filter Opportunities
                    </CardTitle>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleExport('csv')}
                        className="gap-2"
                      >
                        <Download className="w-4 h-4" />
                        Export CSV
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleExport('json')}
                        className="gap-2"
                      >
                        <Download className="w-4 h-4" />
                        Export JSON
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-4">
                    <div className="flex-1 min-w-[200px]">
                      <Input
                        placeholder="Search opportunities..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="max-w-md"
                      />
                    </div>
                    <Select value={filterSource} onValueChange={setFilterSource}>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Source" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Sources</SelectItem>
                        <SelectItem value="YC">YC</SelectItem>
                        <SelectItem value="Product Hunt">Product Hunt</SelectItem>
                        <SelectItem value="Crunchbase">Crunchbase</SelectItem>
                        <SelectItem value="URL Analysis">URL Analysis</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={filterStatus} onValueChange={setFilterStatus}>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="New">New</SelectItem>
                        <SelectItem value="Validating">Validating</SelectItem>
                        <SelectItem value="Building">Building</SelectItem>
                        <SelectItem value="Sold">Sold</SelectItem>
                        <SelectItem value="Declined">Declined</SelectItem>
                      </SelectContent>
                    </Select>
                    <div className="flex items-center gap-2">
                      <Label className="text-sm whitespace-nowrap">Min Score:</Label>
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={filterMinScore}
                        onChange={(e) => setFilterMinScore(parseInt(e.target.value) || 0)}
                        className="w-20"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Opportunities List */}
              <div className="grid gap-4">
                {filteredOpportunities.map((opportunity) => (
                  <Card
                    key={opportunity.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => setSelectedOpportunity(opportunity)}
                  >
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <CardTitle className="text-xl">{opportunity.title}</CardTitle>
                            <Badge className={getStatusColor(opportunity.status)}>
                              {opportunity.status}
                            </Badge>
                            <Badge variant="outline">{opportunity.globalSource}</Badge>
                          </div>
                          <CardDescription className="text-base">
                            {opportunity.description}
                          </CardDescription>
                        </div>
                        <div className={`px-4 py-2 rounded-lg ${getScoreBgColor(opportunity.successScore)}`}>
                          <div className={`text-2xl font-bold ${getScoreColor(opportunity.successScore)}`}>
                            {opportunity.successScore}%
                          </div>
                          <div className="text-xs text-slate-700 dark:text-slate-300">
                            Success Score
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-sm text-slate-700 dark:text-slate-300">
                          <div className="flex items-center gap-1">
                            <Globe className="w-4 h-4" />
                            <span>{opportunity.globalReference}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            <span>{new Date(opportunity.createdAt).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm">
                          View Details
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Knowledge Graph Tab */}
            <TabsContent value="knowledge-graph" className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Building2 className="w-5 h-5" />
                        Indian Startup Knowledge Graph
                      </CardTitle>
                      <CardDescription>
                        Track Indian startups to identify market gaps and saturation points
                      </CardDescription>
                    </div>
                    <Dialog open={isAddStartupOpen} onOpenChange={setIsAddStartupOpen}>
                      <DialogTrigger asChild>
                        <Button className="gap-2">
                          <Plus className="w-4 h-4" />
                          Add Startup
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Add Indian Startup</DialogTitle>
                          <DialogDescription>
                            Add an Indian startup to the knowledge graph for gap detection
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div>
                            <Label>Startup Name</Label>
                            <Input
                              placeholder="e.g., Razorpay"
                              value={newStartup.name}
                              onChange={(e) => setNewStartup({ ...newStartup, name: e.target.value })}
                            />
                          </div>
                          <div>
                            <Label>Description</Label>
                            <Textarea
                              placeholder="Describe what the startup does..."
                              value={newStartup.description}
                              onChange={(e) => setNewStartup({ ...newStartup, description: e.target.value })}
                            />
                          </div>
                          <div>
                            <Label>Category</Label>
                            <Input
                              placeholder="e.g., Fintech"
                              value={newStartup.category}
                              onChange={(e) => setNewStartup({ ...newStartup, category: e.target.value })}
                            />
                          </div>
                          <div>
                            <Label>Website (Optional)</Label>
                            <Input
                              placeholder="https://..."
                              value={newStartup.website}
                              onChange={(e) => setNewStartup({ ...newStartup, website: e.target.value })}
                            />
                          </div>
                          <Button onClick={handleAddStartup} className="w-full">
                            Add Startup
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {indianStartups.map((startup) => (
                      <Card key={startup.id} className="hover:shadow-md transition-shadow">
                        <CardHeader>
                          <CardTitle className="text-lg">{startup.name}</CardTitle>
                          <CardDescription>{startup.description}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Badge variant="secondary">{startup.category}</Badge>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* MVP Generator Tab */}
            <TabsContent value="mvp-generator" className="space-y-4">
              {selectedMVP ? (
                <MVPRoadmap
                  roadmap={selectedMVP}
                  onGenerate={() => {
                    setSelectedMVP(null)
                    setActiveTab('opportunities')
                  }}
                />
              ) : (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Rocket className="w-5 h-5" />
                      MVP Generator
                    </CardTitle>
                    <CardDescription>
                      Generate localized MVP roadmaps for high-potential opportunities
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="text-center py-12">
                      <div className="mx-auto w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/20 flex items-center justify-center mb-4">
                        <Lightbulb className="w-8 h-8 text-emerald-600" />
                      </div>
                      <h2 className="text-lg font-semibold mb-2">Select an Opportunity</h2>
                      <p className="text-slate-700 dark:text-slate-300 mb-4 max-w-md mx-auto">
                        Choose an opportunity from the Opportunities tab to generate a comprehensive MVP roadmap tailored for the Indian market.
                      </p>
                      <Button onClick={() => setActiveTab('opportunities')}>
                        Browse Opportunities
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </main>

        {/* Opportunity Detail Modal */}
        {selectedOpportunity && (
          <Dialog open={!!selectedOpportunity} onOpenChange={() => setSelectedOpportunity(null)}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <DialogTitle className="text-2xl">{selectedOpportunity.title}</DialogTitle>
                  <div className={`px-4 py-2 rounded-lg ${getScoreBgColor(selectedOpportunity.successScore)}`}>
                    <div className={`text-xl font-bold ${getScoreColor(selectedOpportunity.successScore)}`}>
                      {selectedOpportunity.successScore}%
                    </div>
                  </div>
                </div>
                <DialogDescription className="text-base">
                  {selectedOpportunity.description}
                </DialogDescription>
              </DialogHeader>

              <ScrollArea className="h-full">
                <div className="space-y-6 pr-4">
                  {/* Source Information */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Source Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-slate-600" />
                        <span className="font-medium">Source:</span>
                        <Badge>{selectedOpportunity.globalSource}</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <ExternalLink className="w-4 h-4 text-slate-600" />
                        <span className="font-medium">Reference:</span>
                        <span className="text-slate-700 dark:text-slate-300">
                          {selectedOpportunity.globalReference}
                        </span>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Scoring Breakdown */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Success Probability Breakdown</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <CheckCircle className="w-4 h-4 text-emerald-600" />
                            Cultural Fit
                          </span>
                          <span className="font-medium">{selectedOpportunity.culturalFit}%</span>
                        </div>
                        <Progress value={selectedOpportunity.culturalFit || 0} className="h-2" />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <Zap className="w-4 h-4 text-amber-600" />
                            Execution Feasibility
                          </span>
                          <span className="font-medium">{selectedOpportunity.executionFeasibility}%</span>
                        </div>
                        <Progress value={selectedOpportunity.executionFeasibility || 0} className="h-2" />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <DollarSign className="w-4 h-4 text-emerald-600" />
                            Payment Readiness
                          </span>
                          <span className="font-medium">{selectedOpportunity.paymentReadiness}%</span>
                        </div>
                        <Progress value={selectedOpportunity.paymentReadiness || 0} className="h-2" />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <Clock className="w-4 h-4 text-blue-600" />
                            Timing Alignment
                          </span>
                          <span className="font-medium">{selectedOpportunity.timingAlignment}%</span>
                        </div>
                        <Progress value={selectedOpportunity.timingAlignment || 0} className="h-2" />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <BarChart3 className="w-4 h-4 text-purple-600" />
                            Monopoly Potential
                          </span>
                          <span className="font-medium">{selectedOpportunity.monopolyPotential}%</span>
                        </div>
                        <Progress value={selectedOpportunity.monopolyPotential || 0} className="h-2" />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <Target className="w-4 h-4 text-orange-600" />
                            Logistics Complexity
                          </span>
                          <span className="font-medium">{selectedOpportunity.logisticsComplexity}%</span>
                        </div>
                        <Progress value={selectedOpportunity.logisticsComplexity || 0} className="h-2" />
                      </div>

                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-red-600" />
                            Regulatory Risk
                          </span>
                          <span className="font-medium">{selectedOpportunity.regulatoryRisk}%</span>
                        </div>
                        <Progress value={selectedOpportunity.regulatoryRisk || 0} className="h-2" />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Gap Analysis */}
                  {selectedOpportunity.gapAnalysis && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Gap Analysis</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-slate-700 dark:text-slate-300">
                          {selectedOpportunity.gapAnalysis}
                        </p>
                      </CardContent>
                    </Card>
                  )}

                  {/* Indian Competitors */}
                  {selectedOpportunity.indianCompetitors && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Indian Competitors</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p className="text-slate-700 dark:text-slate-300">
                          {selectedOpportunity.indianCompetitors}
                        </p>
                      </CardContent>
                    </Card>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3">
                    <Button
                      className="flex-1 gap-2"
                      onClick={() => handleGenerateMVP(selectedOpportunity)}
                      disabled={generatingMVP}
                    >
                      <Rocket className="w-4 h-4" />
                      {generatingMVP ? 'Generating...' : 'Generate MVP Roadmap'}
                    </Button>
                    <Button variant="outline" className="flex-1 gap-2">
                      <Plus className="w-4 h-4" />
                      Add to Pipeline
                    </Button>
                  </div>
                </div>
              </ScrollArea>
            </DialogContent>
          </Dialog>
        )}

        {/* Footer */}
        <footer className="border-t bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm mt-12 py-6">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                  <Target className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  Opportunity Discovery Engine © 2025
                </span>
              </div>
              <div className="flex items-center gap-6 text-sm text-slate-700 dark:text-slate-300">
                <span className="flex items-center gap-1">
                  <TrendingUp className="w-4 h-4" />
                  {stats.total} opportunities discovered
                </span>
                <span className="flex items-center gap-1">
                  <Star className="w-4 h-4" />
                  {stats.highPotential} high-potential
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  )
}
