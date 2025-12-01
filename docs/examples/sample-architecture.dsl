workspace "docs-pipeline" "Sample architecture for demo" {
    model {
        user = person "Technical Writer" "Creates documentation"
        
        system = softwareSystem "docs-pipeline" "Documentation Pipeline" {
            cli = container "CLI" "Command-line interface" "Python"
            orchestrator = container "Orchestrator" "Workflow coordinator" "Python"
            pdfgen = container "PDF Generator" "Document rendering" "Playwright"
            diagrams = container "Diagram Generator" "Architecture visualization" "Structurizr"
            
            user -> cli "Runs pipeline with YAML config"
            cli -> orchestrator "Loads configuration"
            orchestrator -> diagrams "Generates architecture diagrams"
            orchestrator -> pdfgen "Converts markdown to PDF"
        }
    }
    
    views {
        systemContext system "SystemContext" {
            include *
            autolayout lr
        }
        
        container system "Containers" {
            include *
            autolayout lr
        }
        
        theme default
    }
}

