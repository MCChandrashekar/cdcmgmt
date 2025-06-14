

document.addEventListener('DOMContentLoaded', () => {
    try {
        console.log('Initializing visualization...');
        
        if (!hostData || !storageData) {
            throw new Error('Required data not found');
        }
        
        new TreeVisualization('#tree-svg', hostData, storageData);
    } catch (error) {
        console.error('Error initializing visualization:', error);
        document.querySelector('#tree-svg').innerHTML = 
            `<text x="50%" y="50%" text-anchor="middle">Error loading visualization: ${error.message}</text>`;
    }
});

class TreeVisualization {
    constructor(containerId, hostData, storageData) {
        this.containerId = containerId;
        this.hostData = hostData;
        this.storageData = storageData;
        this.width = window.innerWidth - 100;
        this.height = 800;
        this.nodeSpacing = 60;
        this.nodeWidth = 120;
        this.nodeHeight = 50;
        this.initialize();
    }

    initialize() {
        const container = d3.select(this.containerId);
        container.selectAll("*").remove();

        // Create main SVG
        this.svg = container
            .attr('width', this.width)
            .attr('height', this.height);

        // Create main visualization group
        this.g = this.svg.append('g')
            .attr('class', 'main-group');

        // Setup zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Process hierarchies
        this.processHierarchies();
        this.update(this.hostRoot);
    }

    processHierarchies() {
        // Create hierarchies
        this.hostRoot = d3.hierarchy(this.hostData);
        this.storageRoot = d3.hierarchy(this.storageData);

        // Initialize collapse state for non-leaf nodes
        [this.hostRoot, this.storageRoot].forEach(root => {
            root.descendants().forEach(d => {
                if (d.children && !this.isLeafNode(d)) {
                    d._children = d.children;
                    d.children = null;
                    d.state = 'collapsed';
                }
            });

            // Expand root nodes initially
            if (root._children) {
    root.children = root._children;
    root._children = null;
    root.state = 'expanded';
}

        });

        this.updateLayout();
    }

   updateLayout() {
    const treeLayout = d3.tree()
        .nodeSize([this.nodeSpacing + this.nodeHeight, 180])
        .separation((a, b) => a.parent === b.parent ? 1.5 : 2);

    // Layout host tree (left side)
    treeLayout(this.hostRoot);
    this.hostRoot.descendants().forEach(d => {
        d.x += this.height / 4;
        // Host tree grows left to right from y=0
        // d.y stays as is
    });

    // Layout storage tree (right side)
    treeLayout(this.storageRoot);
    
    // Add large offset to push storage tree farther right
    const hostTreeMaxY = Math.max(...this.hostRoot.descendants().map(d => d.y));
    const storageMinGap = 200; // <-- minimum horizontal gap between trees

    this.storageRoot.descendants().forEach(d => {
        d.x += this.height / 4;
        d.y += hostTreeMaxY + storageMinGap;
    });
}


    drawTrees() {
        // Clear and create layers
        this.g.selectAll('*').remove();
        const linkLayer = this.g.append('g').attr('class', 'tree-links-layer');
        const zoningLayer = this.g.append('g').attr('class', 'zoning-links-layer');
        const nodeLayer = this.g.append('g').attr('class', 'nodes-layer');

        const links = [...this.hostRoot.links(), ...this.storageRoot.links()];
        const nodes = [...this.hostRoot.descendants(), ...this.storageRoot.descendants()];

        // Draw tree links
        linkLayer.selectAll('.link')
            .data(links)
            .join('path')
            .attr('class', d => {
                if (d.source.data.type === 'host') return 'link host-link';
                if (d.source.data.type === 'controller') return 'link controller-link';
                return 'link default-link';
            })
            .attr('d', d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x));

        // Draw zoning connections
        this.drawZoningConnections(zoningLayer);

        // Draw nodes
        const nodeGroups = nodeLayer.selectAll('.node')
            .data(nodes)
            .join('g')
            .attr('class', d => {
                const typeClass = d.data.type || '';
                const stateClass = this.isLeafNode(d) ? '' : 
                                 (d.children ? 'expanded' : 'collapsed');
                return `node ${typeClass} ${stateClass}`.trim();
            })
            .attr('transform', d => `translate(${d.y},${d.x})`)
            .on('click', (event, d) => this.click(event, d))
            .on('mouseover', (event, d) => this.showTooltip(event, d))
            .on('mouseout', () => this.hideTooltip());

        // Add node rectangles
        nodeGroups.append('rect')
            .attr('width', this.nodeWidth)
            .attr('height', this.nodeHeight)
            .attr('x', -this.nodeWidth/2)
            .attr('y', -this.nodeHeight/2);

        // Add node labels
        this.addNodeLabels(nodeGroups);
    }

    drawZoningConnections(zoningLayer) {
        const hostSideMembers = this.hostRoot.descendants()
            .filter(d => ['host', 'portal'].includes(d.data.type));
        const storageSideMembers = this.storageRoot.descendants()
            .filter(d => ['subsystem', 'controller'].includes(d.data.type));

        hostSideMembers.forEach(source => {
            if (source.data.connections) {
                source.data.connections.forEach(targetId => {
                    let target = storageSideMembers.find(d => 
                        (d.data.type === 'subsystem' && d.data.nqn === targetId) ||
                        (d.data.type === 'controller' && d.data.details?.ip === targetId)
                    );

                    if (target) {
                        zoningLayer.append('path')
                            .attr('class', 'link zoning')
                            .attr('d', d3.linkHorizontal()
                                .x(d => d.y)
                                .y(d => d.x)({
                                    source: source,
                                    target: target
                                }));
                    }
                });
            }
        });
    }

    addNodeLabels(nodeGroups) {
    const textGroups = nodeGroups.append('g')
        .attr('class', 'node-text');

    const lineOffset = 7; // Small vertical padding from center

    // Line 1: Type label (above center)
    textGroups.append('text')
        .attr('y', -lineOffset)
        .attr('text-anchor', 'middle')
        .attr('alignment-baseline', 'middle')
        .text(d => this.getNodeTypeLabel(d));

    // Line 2: Detail label (below center)
    textGroups.append('text')
        .attr('y', lineOffset)
        .attr('text-anchor', 'middle')
        .attr('alignment-baseline', 'middle')
        .text(d => this.getNodeDetailLabel(d));
}



    getNodeTypeLabel(d) {
    switch (d.data.type) {
        case 'host-root': return 'Host';
        case 'storage-root': return 'Storage Array';
        case 'host': return 'Host NQN';
        case 'portal': return 'Host IPAddr';
        case 'array': return `Array: ${d.data.details?.vendor || ''}`;
        case 'controller': return 'Controller IP';
        case 'subsystem': return 'Subsystem';
        default: return '';
    }
}


    getNodeDetailLabel(d) {
        switch (d.data.type) {
            case 'host':
            case 'subsystem':
                return this.formatNQN(d.data.nqn);
            case 'portal':
            case 'controller':
                return d.data.details?.ip;
            default:
                return '';
        }
    }

    formatNQN(nqn) {
        if (!nqn) return '';
        if (nqn.length <= 15) return nqn;
        return `${nqn.substring(0, 10)}...${nqn.substring(nqn.length - 5)}`;
    }

    isLeafNode(d) {
        return d.data.type === 'portal' || d.data.type === 'subsystem';
    }

    showTooltip(event, d) {
        const tooltip = d3.select('body').selectAll('.tooltip')
            .data([null])
            .join('div')
            .attr('class', 'tooltip')
            .style('opacity', 0);

        const content = [
            `Type: ${d.data.type.toUpperCase()}`,
            d.data.nqn ? `NQN: ${d.data.nqn}` : null,
            ...Object.entries(d.data.details || {}).map(([k, v]) => `${k}: ${v}`),
            d.data.connections ? `Connections: ${d.data.connections.join(', ')}` : null
        ].filter(Boolean).join('<br/>');

        tooltip.html(content)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px')
            .transition()
            .duration(200)
            .style('opacity', 0.9);
    }

    hideTooltip() {
        d3.selectAll('.tooltip')
            .transition()
            .duration(500)
            .style('opacity', 0)
            .remove();
    }

    click(event, d) {
        if (this.isLeafNode(d)) return;

        event.stopPropagation();

        if (d.children) {
            // Collapse
            d._children = d.children;
            d.children = null;
            d.state = 'collapsed';
        } else {
            // Expand
            d.children = d._children;
            d._children = null;
            d.state = 'expanded';

            // Handle overlaps
            const isHostSide = d.data.type === 'host';
            const siblings = isHostSide ? 
                this.hostRoot.descendants().filter(n => n.data.type === 'host') :
                this.storageRoot.descendants().filter(n => n.data.type === 'array');

            if (siblings.length > 3) {
                siblings.forEach(sibling => {
                    if (sibling !== d && sibling.children) {
                        sibling._children = sibling.children;
                        sibling.children = null;
                        sibling.state = 'collapsed';
                    }
                });
            }
        }

        this.updateLayout();
        this.update(d);
    }

    update(source) {
        this.drawTrees();
    }
}