class TreeChart {
    constructor(containerId, data, width = 1200, height = 600) {
        this.containerId = containerId;
        this.data = data;
        this.width = width;
        this.height = height;
        this.margin = {top: 20, right: 120, bottom: 20, left: 120};
        this.nodeWidth = 120;
        this.nodeHeight = 40;
        this.nodeId = 0;
        this.maxVisibleChildren = 10;  // Maximum number of visible children before collapsing
        this.minimapSize = {
            width: Math.max(width/5, 240),
            height: Math.max(height/5, 120)
        };
        this.currentFocusNode = null;
        
        this.initialize();
    }

    initialize() {
        const container = d3.select(this.containerId);
        container.selectAll("*").remove();
        
        // Create main SVG
        this.svg = container
            .attr('width', this.width)
            .attr('height', this.height)
            .style('border', '1px solid #ccc');  // Added for debugging
            
        this.createTooltip();  // Fixed method name capitalization

        // Create main content group with margin
        this.mainGroup = this.svg.append('g')
            .attr('class', 'main-content')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);
            
        // Create minimap
        this.createMinimap();
        
        // Create zoom container
        this.zoomG = this.mainGroup.append('g')
            .attr('class', 'zoom-container');
            
        // Create tree group
        this.g = this.zoomG.append('g')
            .attr('transform', `translate(0,${(this.height - this.margin.top - this.margin.bottom)/2})`);
            
        // Setup zoom behavior
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                this.zoomG.attr('transform', event.transform);
                this.updateMinimapViewport(event.transform);
            });
            
        this.svg.call(this.zoom);
        
        // Setup tree layout with adjusted size
        this.treeLayout = d3.tree()
            .nodeSize([50,250])
            .separation((a, b) => 0.9);

        // Create hierarchy and process data
        this.root = d3.hierarchy(this.data);
        
        // Generate unique IDs and initialize node states
        this.initializeNodes(this.root);
        
        // Ensure root has its children visible initially
        if (this.root._children) {
            this.root.children = this.root._children;
            this.root._children = null;
        }

        // Initial update
        this.update(this.root);
        this.renderMinimap();
        
        // Initial transform to center the tree
        const initialTransform = d3.zoomIdentity
            .translate(this.width/4, this.height/2)
            .scale(0.8);
        this.svg.call(this.zoom.transform, initialTransform);

        // Debug log to check data
        console.log('Initialized with data:', this.data);
        console.log('Root node:', this.root);
    }
    
    createTooltip() {
        // Create tooltip div if it doesn't exist
        if (!d3.select('#tree-tooltip').node()) {
            d3.select('body').append('div')
                .attr('id', 'tree-tooltip')
                .attr('class', 'tooltip')
                .style('opacity', 0);
        }
    }    

    initializeNodes(node) {
        let id = 0;
        node.descendants().forEach(d => {
            d.id = ++id;
            d._id = d.id;  // Permanent ID for data binding
            if (d.children) {
                d._children = d.children;
                if (d.depth > 0) {  // Collapse all except root
                    d.children = null;
                }
            }
        });
    }
    
    collapseOtherZones(focusNode) {
        if (!focusNode || focusNode.data.type !== 'zone') return;
        
        const zoneNodes = this.root.children;
        if (!zoneNodes) return;
        
        const focusIndex = zoneNodes.findIndex(d => d.id === focusNode.id);
        if (focusIndex === -1) return;
        
        // Collect nodes above focus
        const nodesAbove = zoneNodes.slice(0, focusIndex);
        if (nodesAbove.length > 0) {
            const collapsedAbove = this.createCollapsedNode(
                `${nodesAbove.length} zones above`,
                nodesAbove,
                'above'
            );
            nodesAbove.forEach(n => n.children = null);
        }
        
        // Keep focus node expanded
        focusNode.children = focusNode._children;
        
        // Collect nodes below focus
        const nodesBelow = zoneNodes.slice(focusIndex + 1);
        if (nodesBelow.length > 0) {
            const collapsedBelow = this.createCollapsedNode(
                `${nodesBelow.length} zones below`,
                nodesBelow,
                'below'
            );
            nodesBelow.forEach(n => n.children = null);
        }
    }
    
    createCollapsedNode(name, nodes, position) {
        return {
            id: `collapsed-${position}-${this.nodeId++}`,
            data: {
                name: name,
                type: 'collapsed',
                status: 'collapsed'
            },
            isCollapsed: true,
            collapsedNodes: nodes,
            depth: 1
        };
    }
    
    click(event, d) {
        event.stopPropagation();
        
        if (d.data.type === 'zone') {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else {
                d.children = d._children;
                this.collapseOtherZones(d);
            }
            this.update(d);
        } else if (d.isCollapsed && d.collapsedNodes) {
            d.collapsedNodes.forEach(n => {
                n.children = n._children;
            });
            this.update(this.root);
        }
    }
    
    createMinimap() {
        // Create minimap group
        this.minimapGroup = this.svg.append('g')
            .attr('class', 'minimap')
            .attr('transform', `translate(10,10)`);
            
        // Add minimap background
        this.minimapGroup.append('rect')
            .attr('class', 'minimap-background')
            .attr('width', this.minimapSize.width)
            .attr('height', this.minimapSize.height);
            
        // Create viewport indicator
        this.minimapViewport = this.minimapGroup.append('rect')
            .attr('class', 'minimap-viewport')
            .attr('width', this.minimapSize.width)
            .attr('height', this.minimapSize.height)
            .attr('x', 0)
            .attr('y', 0);
    }

    processHierarchy(node) {
        let id = 0;
        node.descendants().forEach(d => {
            d.id = ++id;
            if (d.children) {
                if (d.children.length > this.maxVisibleChildren) {
                    // Store original children
                    d._allChildren = d.children;
                    // Keep only maxVisibleChildren visible
                    d.children = d.children.slice(0, this.maxVisibleChildren);
                    // Create a special node for collapsed children
                    d.children.push({
                        id: `collapsed-${d.id}`,
                        data: {
                            name: `+${d._allChildren.length - this.maxVisibleChildren} more`,
                            type: 'collapsed',
                            status: d.data.status
                        },
                        isCollapsed: true,
                        parent: d
                    });
                }
            }
        });
    }
    
    renderMinimap() {
        // Clear previous nodes and links
        this.minimapGroup.selectAll('.minimap-node, .minimap-link').remove();
        
        // Create minimap layout
        const minimapLayout = d3.tree()
            .size([this.minimapSize.height - 20, this.minimapSize.width - 20]);
            
        // Create hierarchy for minimap
        const minimapRoot = d3.hierarchy({...this.data});
        const minimapNodes = minimapLayout(minimapRoot);
        
        // Draw links
        this.minimapGroup.selectAll('.minimap-link')
            .data(minimapNodes.links())
            .enter()
            .append('path')
            .attr('class', 'minimap-link')
            .attr('d', d3.linkHorizontal()
                .x(d => d.y + 10)
                .y(d => d.x + 10));
                
        // Draw nodes
        this.minimapGroup.selectAll('.minimap-node')
            .data(minimapNodes.descendants())
            .enter()
            .append('circle')
            .attr('class', d => `minimap-node minimap-${d.data.type || 'default'}`)
            .attr('cx', d => d.y + 10)
            .attr('cy', d => d.x + 10)
            .attr('r', 2);
    }
    
    updateMinimapViewport(transform) {
        if (!this.minimapViewport) return;
        
        const scale = this.minimapSize.width / (this.width - this.margin.left - this.margin.right);
        const vpWidth = (this.width - this.margin.left - this.margin.right) * scale / transform.k;
        const vpHeight = (this.height - this.margin.top - this.margin.bottom) * scale / transform.k;
        
        const vpX = (-transform.x * scale) + 10;
        const vpY = (-transform.y * scale) + 10;
        
        this.minimapViewport
            .attr('width', Math.min(vpWidth, this.minimapSize.width))
            .attr('height', Math.min(vpHeight, this.minimapSize.height))
            .attr('x', vpX)
            .attr('y', vpY);
    }
    
    update(source) {
        // Compute the new tree layout
        const treeData = this.treeLayout(this.root);
        const nodes = treeData.descendants();
        const links = treeData.links();
        
        // Update the nodes
        const node = this.g.selectAll('g.node')
            .data(nodes, d => d.id);
            
        // Enter new nodes
        const nodeEnter = node.enter().append('g')
            .attr('class', d => {
                const statusClass = d.data.status || '';
                const typeClass = d.data.type || '';
                return `node ${typeClass} ${statusClass}`;
            })
            .attr('transform', d => `translate(${source.y0},${source.x0})`)
            .on('click', (event, d) => this.click(event, d))
            .on('mouseover', (event, d) => {
            const tooltip = d3.select('#tree-tooltip');
            tooltip.transition()
                .duration(200)
                .style('opacity', 0.9);
            let tooltipContent = '';
            if (d.data.type === 'root') {
                const zCount = d.children ? d.children.length : 0;
                tooltipContent = `ZoneGroup ID: ${d.data.id || 'N/A'}<br>Zone Count: ${zCount}`;
            } else if (d.data.type === 'zone') {
                const aliasCount = d.children ? d.children.length : 0;
                tooltipContent = `Zone ID: ${d.data.id || 'N/A'}<br>Alias Count: ${aliasCount}`;
            } else if (d.data.type === 'alias') {
                // Fix: Access the correct properties in AliasMembers
                tooltipContent = `${d.data.Type || 'Unknown'}`;
                if (d.data.IPAddress) {
                    tooltipContent += `: ${d.data.IPAddress}`;
                }
                if (d.data.NQN) {
                    tooltipContent += `<br>${d.data.NQN}`;
                }
            }

            if (!tooltipContent) {
                tooltipContent = 'No Data Available';
            }

            tooltip.html(tooltipContent)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 28) + 'px');
            })
            .on('mousemove', (event) => {
                const tooltip = d3.select('#tree-tooltip');
                tooltip.style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', () => {
                const tooltip = d3.select('#tree-tooltip')
                    .transition()
                    .duration(500)
                    .style('opacity', 0);
            });
            
        // Add Rectangle
        nodeEnter.append('rect')
            .attr('width', this.nodeWidth)
            .attr('height', this.nodeHeight)
            .attr('x', -this.nodeWidth/2)
            .attr('y', -this.nodeHeight/2)
            .attr('class', d => d.isCollapsed ? 'collapsed' : '');
            
        // Add Text
        nodeEnter.append('text')
            .attr('dy', '.35em')
            .attr('x', 0)
            .attr('text-anchor', 'middle')
            .text(d => d.data.name)
            .attr('class', d => d.isCollapsed ? 'collapsed-text' : '');
            
        // Add expand/collapse icon if not a collapsed node
        nodeEnter.filter(d => !d.isCollapsed)
            .append('text')
            .attr('class', 'expand-icon')
            .attr('x', this.nodeWidth/2 - 15)
            .attr('dy', '.35em')
            .text(d => d.children || d._children ? (d.children ? '-' : '+') : '');
            
        // Update
        const nodeUpdate = nodeEnter.merge(node);
        nodeUpdate.transition()
            .duration(750)
            .attr('transform', d => `translate(${d.y},${d.x})`);
            
        // Exit
        node.exit().transition()
            .duration(750)
            .attr('transform', d => `translate(${source.y},${source.x})`)
            .remove();
            
        // Update links
        const link = this.g.selectAll('path.link')
            .data(links, d => d.target.id);
            
        link.enter().insert('path', 'g')
            .attr('class', 'link')
            .attr('d', d => {
                const o = {x: source.x0, y: source.y0};
                return this.diagonal(o, o);
            })
            .merge(link)
            .transition()
            .duration(750)
            .attr('d', d => this.diagonal(d.source, d.target));
            
        link.exit().transition()
            .duration(750)
            .attr('d', d => {
                const o = {x: source.x, y: source.y};
                return this.diagonal(o, o);
            })
            .remove();
            
        // Store positions for transitions
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
}