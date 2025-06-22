/**
 * Interactive Git Repository Tree Explorer
 * Uses D3.js for visualization with game-like features
 */

class TreeExplorer {
    constructor() {
        this.data = null;
        this.svg = null;
        this.g = null;
        this.tree = null;
        this.root = null;
        this.exploredNodes = new Set();
        this.currentNode = null;
        this.nodeId = 0;
        
        // Configuration
        this.config = {
            width: 800,
            height: 600,
            margin: { top: 20, right: 20, bottom: 20, left: 20 },
            minFontSize: 8,
            maxFontSize: 24,
            nodeRadius: 8,
            sizeMode: 'ranked' // 'ranked' or 'proportional'
        };
        
        // Color palette for file extensions
        this.colorPalette = {
            'directory': '#6366f1',
            '.js': '#f7df1e',
            '.ts': '#3178c6',
            '.py': '#3776ab',
            '.java': '#ed8b00',
            '.cpp': '#00599c',
            '.c': '#a8b9cc',
            '.cs': '#239120',
            '.php': '#777bb4',
            '.rb': '#cc342d',
            '.go': '#00add8',
            '.rs': '#000000',
            '.swift': '#fa7343',
            '.kt': '#7f52ff',
            '.scala': '#dc322f',
            '.html': '#e34f26',
            '.css': '#1572b6',
            '.scss': '#cc6699',
            '.json': '#000000',
            '.xml': '#0060ac',
            '.yml': '#cb171e',
            '.yaml': '#cb171e',
            '.md': '#083fa1',
            '.txt': '#808080',
            '.pdf': '#ff0000',
            '.jpg': '#ff6b6b',
            '.png': '#4ecdc4',
            '.gif': '#45b7d1',
            '.svg': '#ff9f43',
            'default': '#95a5a6'
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupSVG();
    }
    
    setupEventListeners() {
        // Form submission
        document.getElementById('treeForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFormSubmit();
        });
        
        // Search functionality
        document.getElementById('searchBox').addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });
        
        // Size controls
        document.getElementById('minSizeSlider').addEventListener('input', (e) => {
            this.config.minFontSize = parseInt(e.target.value);
            document.getElementById('minSizeValue').textContent = e.target.value + 'px';
            this.updateNodeSizes();
        });
        
        document.getElementById('maxSizeSlider').addEventListener('input', (e) => {
            this.config.maxFontSize = parseInt(e.target.value);
            document.getElementById('maxSizeValue').textContent = e.target.value + 'px';
            this.updateNodeSizes();
        });
        
        // Size mode selection
        document.querySelectorAll('input[name="sizeMode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.config.sizeMode = e.target.value;
                this.updateNodeSizes();
            });
        });
        
        // Reset button
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetView();
        });
    }
    
    setupSVG() {
        this.svg = d3.select('#treeSvg');
        this.g = this.svg.append('g');
        
        // Add zoom and pan behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });
        
        this.svg.call(zoom);
    }
    
    async handleFormSubmit() {
        const formData = new FormData(document.getElementById('treeForm'));
        const repoUrl = formData.get('repo_url');
        const token = formData.get('token');
        
        if (!repoUrl) {
            this.showError('Please enter a repository URL');
            return;
        }
        
        this.showLoading(true);
        this.clearError();
        
        try {
            const response = await fetch('/api/tree-data', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.data = result.data;
                this.setupTree();
                this.showRepoInfo(result.repo_info);
                document.getElementById('controls').classList.remove('hidden');
                document.getElementById('infoPanel').classList.remove('hidden');
            } else {
                this.showError(result.error || 'Failed to load repository');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }
    
    setupTree() {
        // Clear existing tree
        this.g.selectAll('*').remove();
        
        // Setup tree layout
        this.tree = d3.tree()
            .size([this.config.height - 40, this.config.width - 40])
            .separation((a, b) => (a.parent === b.parent ? 1 : 2) / a.depth);
        
        // Create hierarchy
        this.root = d3.hierarchy(this.data);
        this.root.x0 = this.config.height / 2;
        this.root.y0 = 0;
        
        // Initially collapse all nodes except root
        this.root.children.forEach(this.collapse);
        
        this.update(this.root);
    }
    
    collapse = (d) => {
        if (d.children) {
            d._children = d.children;
            d._children.forEach(this.collapse);
            d.children = null;
        }
    }
    
    update(source) {
        const treeData = this.tree(this.root);
        const nodes = treeData.descendants();
        const links = treeData.descendants().slice(1);
        
        // Normalize for fixed-depth
        nodes.forEach(d => { d.y = d.depth * 180; });
        
        // Update nodes
        const node = this.g.selectAll('g.node')
            .data(nodes, d => d.id || (d.id = ++this.nodeId));
        
        // Enter new nodes
        const nodeEnter = node.enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${source.y0},${source.x0})`)
            .on('click', (event, d) => this.handleNodeClick(event, d));
        
        // Add circles for nodes
        nodeEnter.append('circle')
            .attr('class', 'node-circle')
            .attr('r', this.config.nodeRadius)
            .style('fill', d => this.getNodeColor(d.data))
            .style('opacity', d => this.exploredNodes.has(d.data.path) ? 1 : 0.5);
        
        // Add text labels
        nodeEnter.append('text')
            .attr('class', 'node-text')
            .attr('dy', '0.35em')
            .attr('x', d => d.children || d._children ? -13 : 13)
            .style('text-anchor', d => d.children || d._children ? 'end' : 'start')
            .style('font-size', d => this.getNodeFontSize(d.data) + 'px')
            .text(d => d.data.name);
        
        // Update existing nodes
        const nodeUpdate = nodeEnter.merge(node);
        
        nodeUpdate.transition()
            .duration(750)
            .attr('transform', d => `translate(${d.y},${d.x})`);
        
        nodeUpdate.select('circle.node-circle')
            .style('fill', d => this.getNodeColor(d.data))
            .style('opacity', d => this.exploredNodes.has(d.data.path) ? 1 : 0.5);
        
        // Remove exiting nodes
        const nodeExit = node.exit().transition()
            .duration(750)
            .attr('transform', d => `translate(${source.y},${source.x})`)
            .remove();
        
        nodeExit.select('circle')
            .attr('r', 1e-6);
        
        nodeExit.select('text')
            .style('fill-opacity', 1e-6);
        
        // Update links
        const link = this.g.selectAll('path.link')
            .data(links, d => d.id);
        
        // Enter new links
        const linkEnter = link.enter().insert('path', 'g')
            .attr('class', 'link')
            .attr('d', d => {
                const o = { x: source.x0, y: source.y0 };
                return this.diagonal(o, o);
            });
        
        // Update existing links
        const linkUpdate = linkEnter.merge(link);
        
        linkUpdate.transition()
            .duration(750)
            .attr('d', d => this.diagonal(d, d.parent));
        
        // Remove exiting links
        link.exit().transition()
            .duration(750)
            .attr('d', d => {
                const o = { x: source.x, y: source.y };
                return this.diagonal(o, o);
            })
            .remove();
        
        // Store old positions for transition
        nodes.forEach(d => {
            d.x0 = d.x;
            d.y0 = d.y;
        });
    }
    
    diagonal(s, d) {
        return `M ${s.y} ${s.x}
                C ${(s.y + d.y) / 2} ${s.x},
                  ${(s.y + d.y) / 2} ${d.x},
                  ${d.y} ${d.x}`;
    }
    
    handleNodeClick(event, d) {
        if (d.children) {
            d._children = d.children;
            d.children = null;
        } else {
            d.children = d._children;
            d._children = null;
        }
        
        // Mark as explored
        this.exploredNodes.add(d.data.path);
        
        // Update current node info
        this.showNodeInfo(d.data);
        
        this.update(d);
    }
    
    getNodeColor(nodeData) {
        if (nodeData.type === 'directory') {
            return this.colorPalette['directory'];
        }
        
        const extension = nodeData.extension || '';
        return this.colorPalette[extension] || this.colorPalette['default'];
    }
    
    getNodeFontSize(nodeData) {
        if (nodeData.type === 'directory') {
            return this.config.minFontSize + 2;
        }
        
        if (this.config.sizeMode === 'ranked') {
            // Simple ranking based on file size
            const size = nodeData.size || 0;
            if (size < 1000) return this.config.minFontSize;
            if (size < 10000) return this.config.minFontSize + 2;
            if (size < 100000) return this.config.minFontSize + 4;
            return this.config.maxFontSize;
        } else {
            // Proportional sizing
            const maxSize = Math.max(...this.getAllFileSizes());
            const proportion = (nodeData.size || 0) / maxSize;
            return this.config.minFontSize + (proportion * (this.config.maxFontSize - this.config.minFontSize));
        }
    }
    
    getAllFileSizes() {
        const sizes = [];
        const traverse = (node) => {
            if (node.type === 'file') {
                sizes.push(node.size || 0);
            }
            if (node.children) {
                node.children.forEach(traverse);
            }
        };
        traverse(this.data);
        return sizes;
    }
    
    updateNodeSizes() {
        this.g.selectAll('text.node-text')
            .style('font-size', d => this.getNodeFontSize(d.data) + 'px');
    }
    
    handleSearch(query) {
        if (!query.trim()) {
            // Reset all nodes
            this.g.selectAll('.node').style('opacity', 1);
            return;
        }
        
        const searchLower = query.toLowerCase();
        this.g.selectAll('.node')
            .style('opacity', d => {
                return d.data.name.toLowerCase().includes(searchLower) ? 1 : 0.3;
            });
    }
    
    resetView() {
        this.svg.transition().duration(750).call(
            d3.zoom().transform,
            d3.zoomIdentity
        );
        
        // Reset search
        document.getElementById('searchBox').value = '';
        this.handleSearch('');
    }
    
    showRepoInfo(repoInfo) {
        const repoDetails = document.getElementById('repoDetails');
        repoDetails.innerHTML = `
            <div><strong>Repository:</strong> ${repoInfo.slug}</div>
            <div><strong>Files:</strong> ${repoInfo.total_files}</div>
            <div><strong>Directories:</strong> ${repoInfo.total_dirs}</div>
        `;
    }
    
    showNodeInfo(nodeData) {
        const nodeInfo = document.getElementById('nodeInfo');
        const nodeDetails = document.getElementById('nodeDetails');
        
        nodeDetails.innerHTML = `
            <div><strong>Name:</strong> ${nodeData.name}</div>
            <div><strong>Type:</strong> ${nodeData.type}</div>
            <div><strong>Size:</strong> ${this.formatBytes(nodeData.size || 0)}</div>
            ${nodeData.extension ? `<div><strong>Extension:</strong> ${nodeData.extension}</div>` : ''}
            <div><strong>Path:</strong> ${nodeData.path}</div>
        `;
        
        nodeInfo.classList.remove('hidden');
    }
    
    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showLoading(show) {
        document.getElementById('loading').classList.toggle('hidden', !show);
    }
    
    showError(message) {
        const errorContainer = document.getElementById('errorContainer');
        errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
    }
    
    clearError() {
        document.getElementById('errorContainer').innerHTML = '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TreeExplorer();
});