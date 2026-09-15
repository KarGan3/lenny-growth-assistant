import { Component } from 'react'

export default class ArtifactBoundary extends Component {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  componentDidCatch(error) {
    console.error('Artifact preview failed', { name: error.name })
  }
  render() {
    if (this.state.failed) {
      return <div role="alert" className="p-5 text-sm text-danger">
        <p>Could not render this artifact. Close the preview and try generating it again.</p>
        <button type="button" onClick={this.props.onClose} className="mt-3 rounded border border-line p-2">Close preview</button>
      </div>
    }
    return this.props.children
  }
}
