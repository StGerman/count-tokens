#!/usr/bin/env python3
"""
Basic pytest tests for count_tokens.py

Tests the main flows of the token counting functionality without edge cases.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import count_tokens


class TestCountFileTokens:
    """Test counting tokens in individual files."""
    
    def test_count_tokens_simple_text_file(self):
        """Test basic token counting for a simple text file."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "Hello world! This is a test file with some content."
            f.write(test_content)
            temp_file = f.name
        
        try:
            # Mock tiktoken encoding
            mock_encoding = MagicMock()
            mock_encoding.encode.return_value = ['token1', 'token2', 'token3', 'token4', 'token5']
            
            result = count_tokens.count_file_tokens(temp_file, mock_encoding)
            
            assert result == 5
            mock_encoding.encode.assert_called_once_with(test_content)
        finally:
            os.unlink(temp_file)
    
    def test_count_tokens_empty_file(self):
        """Test token counting for an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        try:
            mock_encoding = MagicMock()
            mock_encoding.encode.return_value = []
            
            result = count_tokens.count_file_tokens(temp_file, mock_encoding)
            
            assert result == 0
            mock_encoding.encode.assert_called_once_with("")
        finally:
            os.unlink(temp_file)
    
    def test_count_tokens_nonexistent_file(self):
        """Test handling of nonexistent files."""
        mock_encoding = MagicMock()
        
        # Capture stderr to test warning message
        import io
        import sys
        captured_stderr = io.StringIO()
        
        with patch('sys.stderr', captured_stderr):
            result = count_tokens.count_file_tokens("nonexistent_file.txt", mock_encoding)
        
        assert result == 0
        assert "Warning: Skipped nonexistent_file.txt" in captured_stderr.getvalue()


class TestLoadGitignorePatterns:
    """Test loading .gitignore patterns."""
    
    def test_load_default_patterns(self):
        """Test that default git patterns are always loaded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                patterns = count_tokens.load_gitignore_patterns()
                
                # Test that default .git patterns are included
                assert patterns.match_file('.git/config')
                assert patterns.match_file('some/nested/.git/file')
            finally:
                os.chdir(original_cwd)
    
    def test_load_gitignore_file(self):
        """Test loading patterns from .gitignore file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Create a .gitignore file
                gitignore_path = Path(temp_dir) / '.gitignore'
                gitignore_path.write_text('*.log\n__pycache__/\n# comment\nnode_modules/\n')
                
                patterns = count_tokens.load_gitignore_patterns()
                
                # Test that patterns from .gitignore are loaded
                assert patterns.match_file('debug.log')
                assert patterns.match_file('__pycache__/test.py')
                assert patterns.match_file('node_modules/package.json')
                
                # Test that comments are ignored
                assert not patterns.match_file('# comment')
            finally:
                os.chdir(original_cwd)


class TestGetFilesRespectingGitignore:
    """Test file discovery with .gitignore patterns."""
    
    def test_get_files_basic(self):
        """Test basic file discovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Create some test files
                (Path(temp_dir) / 'test.py').write_text('print("hello")')
                (Path(temp_dir) / 'README.md').write_text('# Test')
                (Path(temp_dir) / 'config.json').write_text('{}')
                
                files = count_tokens.get_files_respecting_gitignore()
                
                expected_files = ['README.md', 'config.json', 'test.py']
                assert sorted(files) == sorted(expected_files)
            finally:
                os.chdir(original_cwd)
    
    def test_get_files_with_gitignore(self):
        """Test file discovery with .gitignore patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                # Create test files
                (Path(temp_dir) / 'test.py').write_text('print("hello")')
                (Path(temp_dir) / 'debug.log').write_text('log data')
                (Path(temp_dir) / 'README.md').write_text('# Test')
                
                # Create .gitignore
                (Path(temp_dir) / '.gitignore').write_text('*.log\n')
                
                files = count_tokens.get_files_respecting_gitignore()
                
                # debug.log should be filtered out, .gitignore should be included
                expected_files = ['.gitignore', 'README.md', 'test.py']
                assert sorted(files) == sorted(expected_files)
                assert 'debug.log' not in files
            finally:
                os.chdir(original_cwd)


class TestCountTokens:
    """Test the main count_tokens function."""
    
    @patch('count_tokens.tiktoken.get_encoding')
    @patch('count_tokens.get_files_respecting_gitignore')
    @patch('count_tokens.count_file_tokens')
    def test_count_tokens_basic(self, mock_count_file, mock_get_files, mock_get_encoding):
        """Test basic token counting functionality."""
        # Setup mocks
        mock_get_files.return_value = ['test.py', 'script.js', 'README.md', 'data.xml']
        mock_count_file.side_effect = [100, 50, 30, 0]  # Return different token counts
        mock_encoding = MagicMock()
        mock_get_encoding.return_value = mock_encoding
        
        # Capture stdout to test output
        import io
        import sys
        captured_stdout = io.StringIO()
        
        with patch('sys.stdout', captured_stdout):
            count_tokens.count_tokens(
                encoding_name='cl100k_base',
                extensions=('.py', '.js', '.md'),
                show_files=True,
                top_n=3
            )
        
        output = captured_stdout.getvalue()
        
        # Verify mocks were called correctly
        mock_get_encoding.assert_called_once_with('cl100k_base')
        mock_get_files.assert_called_once()
        
        # count_file_tokens should be called for files with matching extensions
        assert mock_count_file.call_count == 3  # .py, .js, .md (not .xml)
        
        # Check output contains expected information
        assert "Total tokens: 180" in output  # 100 + 50 + 30
        assert "Total files: 3" in output
        assert "Average per file: 60 tokens" in output
        
        # Check cost estimates are included
        assert "Cost estimates" in output
        assert "Claude Sonnet 4" in output
    
    @patch('count_tokens.tiktoken.get_encoding')
    @patch('count_tokens.get_files_respecting_gitignore')
    @patch('count_tokens.count_file_tokens')
    def test_count_tokens_no_files_output(self, mock_count_file, mock_get_files, mock_get_encoding):
        """Test token counting with show_files=False."""
        mock_get_files.return_value = ['test.py']
        mock_count_file.return_value = 100
        mock_encoding = MagicMock()
        mock_get_encoding.return_value = mock_encoding
        
        import io
        import sys
        captured_stdout = io.StringIO()
        
        with patch('sys.stdout', captured_stdout):
            count_tokens.count_tokens(
                show_files=False
            )
        
        output = captured_stdout.getvalue()
        
        # Should not show file breakdown
        assert "Top" not in output
        assert "tokens |" not in output
        
        # Should show summary
        assert "Total tokens: 100" in output
        assert "Total files: 1" in output
    
    @patch('count_tokens.tiktoken.get_encoding')
    @patch('count_tokens.get_files_respecting_gitignore')
    @patch('count_tokens.count_file_tokens')
    def test_count_tokens_custom_extensions(self, mock_count_file, mock_get_files, mock_get_encoding):
        """Test token counting with custom file extensions."""
        mock_get_files.return_value = ['script.py', 'style.css', 'data.json', 'README.md']
        mock_count_file.return_value = 25  # Return 25 tokens for the .css file
        mock_encoding = MagicMock()
        mock_get_encoding.return_value = mock_encoding
        
        import io
        import sys
        captured_stdout = io.StringIO()
        
        with patch('sys.stdout', captured_stdout):
            count_tokens.count_tokens(
                extensions=('.css',),  # Only CSS files
                show_files=False
            )
        
        # Should only process .css files
        assert mock_count_file.call_count == 1
        mock_count_file.assert_called_with('style.css', mock_encoding)
        
        output = captured_stdout.getvalue()
        assert "Total tokens: 25" in output
        assert "Total files: 1" in output


class TestMain:
    """Test the main CLI function."""
    
    @patch('count_tokens.count_tokens')
    def test_main_default_args(self, mock_count_tokens):
        """Test main function with default arguments."""
        test_args = ['count-tokens']
        
        with patch('sys.argv', test_args):
            count_tokens.main()
        
        # Verify count_tokens was called with defaults
        mock_count_tokens.assert_called_once_with(
            encoding_name='cl100k_base',
            extensions=count_tokens.DEFAULT_EXTENSIONS,
            show_files=True,
            top_n=30
        )
    
    @patch('count_tokens.count_tokens')
    def test_main_custom_args(self, mock_count_tokens):
        """Test main function with custom arguments."""
        test_args = [
            'count-tokens',
            '--encoding', 'o200k_base',
            '--no-files',
            '--top', '50',
            '--extensions', '.py', '.js'
        ]
        
        with patch('sys.argv', test_args):
            count_tokens.main()
        
        # Verify count_tokens was called with custom args
        mock_count_tokens.assert_called_once_with(
            encoding_name='o200k_base',
            extensions=('.py', '.js'),
            show_files=False,  # --no-files
            top_n=50
        )


class TestConstants:
    """Test module constants and configurations."""
    
    def test_default_extensions(self):
        """Test that default extensions include expected file types."""
        extensions = count_tokens.DEFAULT_EXTENSIONS
        
        # Test some key extensions are included
        assert '.py' in extensions
        assert '.js' in extensions
        assert '.md' in extensions
        assert '.json' in extensions
        assert '.css' in extensions
        
        # Test that extensions is a tuple (required for str.endswith)
        assert isinstance(extensions, tuple)
    
    def test_cost_per_token(self):
        """Test that cost estimates are defined for expected models."""
        costs = count_tokens.COST_PER_TOKEN
        
        # Test some expected models are included
        assert 'Claude Sonnet 4' in costs
        assert 'GPT-4o' in costs
        assert 'GPT-4o mini' in costs
        
        # Test that all costs are positive numbers
        for model, cost in costs.items():
            assert isinstance(cost, (int, float))
            assert cost > 0